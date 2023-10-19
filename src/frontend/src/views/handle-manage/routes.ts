/*
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
*/
export default {
  path: '/handle-manage',
  component: () => import('@views/notice-group/index.vue'),
  name: 'handleManage',
  redirect: {
    name: 'handleManageList',
  },
  meta: {
    navName: 'auditRiskManage',
  },
  children: [
    {
      path: 'list',
      component: () => import('@views/handle-manage/index.vue'),
      name: 'handleManageList',
      meta: {
        title: '待我处理',
        // skeleton: 'noticeGroupList',
      },
    },
    {
      path: 'detail/:riskId',
      component: () => import('@views/risk-manage/detail/index.vue'),
      name: 'handleManageDetail',
      meta: {
        title: '风险详情',
        // skeleton: 'noticeGroupList',
      },
    },
  ],
};
