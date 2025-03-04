# -*- coding: utf-8 -*-
"""
TencentBlueKing is pleased to support the open source community by making
蓝鲸智云 - 审计中心 (BlueKing - Audit Center) available.
Copyright (C) 2023 THL A29 Limited,
a Tencent company. All rights reserved.
Licensed under the MIT License (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
either express or implied. See the License for the
specific language governing permissions and limitations under the License.
We undertake not to change the open source license (MIT license) applicable
to the current version of the project delivered to anyone in the future.
"""

import abc
from typing import List

from bk_resource import api, resource
from blueapps.utils.logger import logger
from blueapps.utils.request_provider import get_request_username
from django.utils.translation import gettext_lazy

from api.bk_base.constants import StorageType
from api.bk_log.constants import INDEX_SET_ID
from apps.audit.resources import AuditMixinResource
from apps.meta.constants import ConfigLevelChoices
from apps.meta.models import GlobalMetaConfig, SensitiveObject
from apps.permission.handlers.actions import ActionEnum
from apps.permission.handlers.permission import Permission
from apps.permission.handlers.resource_types import ResourceEnum
from core.exceptions import PermissionException
from core.permissions import SearchLogPermission
from core.utils.tools import is_product
from services.web.databus.constants import DEFAULT_STORAGE_CONFIG_KEY
from services.web.query.constants import COLLECT_SEARCH_CONFIG, DEFAULT_COLLECTOR_RT_KEY
from services.web.query.serializers import (
    CollectorSearchConfigRespSerializer,
    CollectorSearchReqSerializer,
    EsQueryAttrSerializer,
    EsQuerySearchAttrSerializer,
    FieldMapRequestSerializer,
    QuerySearchResponseSerializer,
)
from services.web.query.utils.collector import CollectorSQLBuilder
from services.web.query.utils.field_map import FieldMapHandler
from services.web.query.utils.formatter import HitsFormatter


class QueryBaseResource(AuditMixinResource, abc.ABC):
    tags = ["Query"]


class EsQueryResource(QueryBaseResource):
    RequestSerializer = EsQueryAttrSerializer

    def perform_request(self, validated_request_data):
        validated_request_data.update(
            {
                "storage_cluster_id": int(
                    validated_request_data.get("storage_cluster_id")
                    or GlobalMetaConfig.get(
                        DEFAULT_STORAGE_CONFIG_KEY,
                        config_level=ConfigLevelChoices.NAMESPACE.value,
                        instance_key=validated_request_data["namespace"],
                    )
                ),
                "index_set_id": (
                    validated_request_data.get("index_set_id")
                    or GlobalMetaConfig.get(
                        INDEX_SET_ID,
                        config_level=ConfigLevelChoices.NAMESPACE.value,
                        instance_key=validated_request_data["namespace"],
                    )
                ),
                "use_time_range": True,
            }
        )
        return api.bk_log.es_query_search(**validated_request_data)


class SearchDataParser:
    def parse_data(self, data: List[dict]) -> list:
        # 获取敏感字段列表
        private_sensitive_objs = list(SensitiveObject._objects.filter(is_private=True))
        sensitive_objs = list(SensitiveObject.objects.all())
        # 获取用户信息，用于判断敏感权限
        if sensitive_objs:
            username = get_request_username()
            if username:
                permissions = Permission(username).batch_is_allowed(
                    actions=[ActionEnum.ACCESS_AUDIT_SENSITIVE_INFO],
                    resources=[[ResourceEnum.SENSITIVE_OBJECT.create_instance(so.id)] for so in sensitive_objs],
                )
            else:
                permissions = {so.id: {ActionEnum.ACCESS_AUDIT_SENSITIVE_INFO: False} for so in sensitive_objs}
            for so in sensitive_objs:
                setattr(
                    so,
                    "_has_permission",
                    permissions.get(so.id, {}).get(ActionEnum.ACCESS_AUDIT_SENSITIVE_INFO.id, False),
                )
        # parse
        return [HitsFormatter(value, [*sensitive_objs, *private_sensitive_objs]).value for value in data]


class SearchAllResource(QueryBaseResource, SearchDataParser):
    name = gettext_lazy("搜索(All)")
    RequestSerializer = EsQuerySearchAttrSerializer
    serializer_class = QuerySearchResponseSerializer

    def perform_request(self, validated_request_data):
        # 调用BK-LOG查询事件
        page = validated_request_data.pop("page")
        num_pages = validated_request_data.pop("page_size")
        resp = resource.query.es_query(**validated_request_data)
        total = resp.get("hits", {}).get("total", 0)
        hits = self.parse_data([hit["_source"] for hit in resp.get("hits", {}).get("hits", [])])
        # 补充系统信息
        if validated_request_data["bind_system_info"]:
            systems = resource.meta.system_list(namespace=validated_request_data["namespace"])
            system_map = {system["system_id"]: system for system in systems}
            for hit in hits:
                hit["system_info"] = system_map.get(hit.get("system_id"), dict())
        # 响应
        return {
            "page": page,
            "num_pages": num_pages,
            "total": total,
            "results": hits,
            "scroll_id": resp.get("_scroll_id"),
        }


class SearchResource(SearchAllResource):
    name = gettext_lazy("搜索")
    RequestSerializer = EsQuerySearchAttrSerializer
    serializer_class = QuerySearchResponseSerializer
    audit_action = ActionEnum.SEARCH_REGULAR_EVENT

    def validate_request_data(self, request_data):
        validated_request_data = super().validate_request_data(request_data)
        # 过滤有权限的系统
        systems, authorized_systems = SearchLogPermission.get_auth_systems(validated_request_data["namespace"])
        if not authorized_systems:
            apply_data, apply_url = Permission().get_apply_data([ActionEnum.SEARCH_REGULAR_EVENT])
            raise PermissionException(
                action_name=ActionEnum.SEARCH_REGULAR_EVENT.name,
                apply_url=apply_url,
                permission=apply_data,
            )
        if len(systems) != len(authorized_systems):
            validated_request_data["filter"].append(
                {
                    "field": "system_id",
                    "operator": "is one of",
                    "value": authorized_systems,
                    "condition": "and",
                    "type": "field",
                }
            )
        return validated_request_data


class FieldMapResource(QueryBaseResource):
    name = gettext_lazy("字段列表")
    RequestSerializer = FieldMapRequestSerializer

    def perform_request(self, validated_request_data):
        SearchLogPermission.any_search_log_permission(validated_request_data["namespace"])
        return FieldMapHandler(**validated_request_data).field_map


class CollectorSearchConfigResource(QueryBaseResource):
    name = gettext_lazy("日志查询配置")
    many_response_data = True
    ResponseSerializer = CollectorSearchConfigRespSerializer

    def perform_request(self, validated_request_data):
        return COLLECT_SEARCH_CONFIG.to_json()


class CollectorSearchResource(QueryBaseResource, SearchDataParser):
    name = gettext_lazy("日志查询")
    RequestSerializer = CollectorSearchReqSerializer
    serializer_class = QuerySearchResponseSerializer

    def build_sql(self, validated_request_data):
        """
        构建日志查询SQL
        """

        page = validated_request_data["page"]
        page_size = validated_request_data["page_size"]
        namespace = validated_request_data["namespace"]
        filters = validated_request_data["filters"]
        collector_rt_id = GlobalMetaConfig.get(
            DEFAULT_COLLECTOR_RT_KEY,
            config_level=ConfigLevelChoices.NAMESPACE.value,
            instance_key=namespace,
        )
        sql_builder = CollectorSQLBuilder(
            table=collector_rt_id,
            filters=filters,
            sort_list=validated_request_data["sort_list"],
            page=page,
            page_size=page_size,
        )
        data_sql = sql_builder.build_data_sql()
        count_sql = sql_builder.build_count_sql()
        logger.info(f"[{self.__class__.__name__}] search data_sql: {data_sql};count_sql:{count_sql}")
        return data_sql, count_sql

    def perform_request(self, validated_request_data):
        page = validated_request_data["page"]
        page_size = validated_request_data["page_size"]
        bind_system_info = validated_request_data["bind_system_info"]
        data_sql, count_sql = self.build_sql(validated_request_data)
        bulk_req_params = [
            {
                "sql": data_sql,
                "prefer_storage": StorageType.DORIS.value,
            },
            {
                "sql": count_sql,
                "prefer_storage": StorageType.DORIS.value,
            },
        ]
        # 请求BKBASE数据
        bulk_resp = api.bk_base.query_sync.bulk_request(bulk_req_params)
        data_resp, count_resp = bulk_resp
        data = self.parse_data(data_resp.get("list", []))
        # 补充系统信息
        if bind_system_info:
            systems = resource.meta.system_list(namespace=validated_request_data["namespace"])
            system_map = {system["system_id"]: system for system in systems}
            for value in data:
                value["system_info"] = system_map.get(value.get("system_id"), dict())
        # 请求总数
        total = count_resp.get("list", [{}])[0].get("count", 0)
        # 响应
        resp = {
            "page": page,
            "num_pages": page_size,
            "total": total,
            "results": data,
        }
        # 非正式环境返回原始SQL
        if not is_product():
            resp.update({"query_sql": data_sql, "count_sql": count_sql})
        return resp
