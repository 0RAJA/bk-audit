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
export default class Event {
  event_id: string;
  event_content: string;
  raw_event_id: string;
  strategy_id: number;
  event_data: Record<string, any>;
  event_time: number;
  event_source: string;
  operator: string;
  event_evidence: string;

  constructor(payload = {} as Event) {
    this.event_content = payload.event_content;
    this.event_id = payload.event_id;
    this.raw_event_id = payload.raw_event_id;
    this.strategy_id = payload.strategy_id;
    this.event_time = payload.event_time;
    this.event_source = payload.event_source;
    this.operator = payload.operator;

    this.event_data = payload.event_data;
    this.event_evidence = payload.event_evidence;
  }
}
