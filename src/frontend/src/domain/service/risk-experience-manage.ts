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
import RiskExperienceManageSource from '../source/risk-experience-manage';

export default {
  /**
   * @desc 获取风险处理经验
   */
  fetchExperience(params: {
    risk_id: string
  }) {
    return RiskExperienceManageSource.getExperience(params)
      .then(({ data }) => data);
  },
  /**
   * @desc 保存风险处理经验
   */
  saveExperience(params: {
    risk_id: string,
    content: string,
  }) {
    return RiskExperienceManageSource.saveExperience(params)
      .then(({ data }) => data);
  },
};
