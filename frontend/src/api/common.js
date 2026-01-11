import axios from 'axios'
import { getApiKey } from '../utils/crypto'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000 // 5分钟超时
})

/**
 * 创建试穿/试戴API工厂函数
 * @param {string} apiPrefix - API路径前缀，如 'accessory-try-on' 或 'clothing-try-on'
 * @returns {Object} 包含所有API方法的对象
 */
export function createTryOnApi(apiPrefix) {
  /**
   * 构建请求头（包含API Key）
   * @returns {Object} 请求头对象
   */
  function buildHeaders() {
    const headers = { 'Content-Type': 'multipart/form-data' }
    const configMethod = localStorage.getItem('configMethod')

    if (configMethod === 'manual') {
      const vlApiKey = getApiKey('vlApiKey')
      const imageApiKey = getApiKey('imageApiKey')

      if (vlApiKey) {
        headers['X-VL-API-Key'] = vlApiKey
      }
      if (imageApiKey) {
        headers['X-Image-API-Key'] = imageApiKey
      }
    }

    return headers
  }

  /**
   * 添加模型参数到FormData
   * @param {FormData} formData - 表单数据对象
   */
  function appendModelParams(formData) {
    const vlModel = localStorage.getItem('vlModel') || 'qwen3-vl-plus'
    const imgGenModel = localStorage.getItem('imgGenModel') || 'wan2.6-image'
    formData.append('vl_model', vlModel)
    formData.append('img_gen_model', imgGenModel)
  }

  return {
    /**
     * 提交任务
     * @param {FormData} formData - 包含图片和参数的表单数据
     * @returns {Promise} 返回任务ID
     */
    async submitTask(formData) {
      const headers = buildHeaders()
      appendModelParams(formData)
      const response = await api.post(`/${apiPrefix}/submit`, formData, { headers })
      return response.data
    },

    /**
     * 查询任务状态
     * @param {string} taskId - 任务ID
     * @returns {Promise} 返回任务状态
     */
    async getTaskStatus(taskId) {
      const response = await api.get(`/${apiPrefix}/status/${taskId}`)
      return response.data
    },

    /**
     * 获取任务结果
     * @param {string} taskId - 任务ID
     * @returns {Promise} 返回任务结果
     */
    async getTaskResult(taskId) {
      const response = await api.get(`/${apiPrefix}/result/${taskId}`)
      return response.data
    },

    /**
     * 删除任务
     * @param {string} taskId - 任务ID
     * @returns {Promise} 返回删除结果
     */
    async deleteTask(taskId) {
      const response = await api.delete(`/${apiPrefix}/task/${taskId}`)
      return response.data
    },

    /**
     * 重新提交任务
     * @param {string} taskId - 任务ID
     * @param {FormData} formData - 包含图片和参数的表单数据
     * @returns {Promise} 返回任务信息
     */
    async resubmitTask(taskId, formData) {
      const headers = buildHeaders()
      appendModelParams(formData)
      const response = await api.put(`/${apiPrefix}/resubmit/${taskId}`, formData, { headers })
      return response.data
    }
  }
}

export default api
