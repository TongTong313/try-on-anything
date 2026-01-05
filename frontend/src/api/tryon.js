import axios from 'axios'
import { getApiKey } from '../utils/crypto'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000 // 5分钟超时，因为图像生成需要较长时间
})

/**
 * 提交试穿任务
 * @param {FormData} formData - 包含图片和参数的表单数据
 * @returns {Promise} 返回任务ID
 */
export async function submitTryOnTask(formData) {
  // 构建请求头
  const headers = { 'Content-Type': 'multipart/form-data' }

  // 检查配置方式
  const configMethod = localStorage.getItem('configMethod')

  // 如果是手动输入模式，添加API Key到请求头
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

  // 添加模型参数到formData
  const vlModel = localStorage.getItem('vlModel') || 'qwen3-vl-plus'
  const imgGenModel = localStorage.getItem('imgGenModel') || 'wan2.6-image'
  formData.append('vl_model', vlModel)
  formData.append('img_gen_model', imgGenModel)

  const response = await api.post('/tryon/submit', formData, { headers })
  return response.data
}

/**
 * 查询任务状态
 * @param {string} taskId - 任务ID
 * @returns {Promise} 返回任务状态
 */
export async function getTaskStatus(taskId) {
  const response = await api.get(`/tryon/status/${taskId}`)
  return response.data
}

/**
 * 获取任务结果
 * @param {string} taskId - 任务ID
 * @returns {Promise} 返回任务结果
 */
export async function getTaskResult(taskId) {
  const response = await api.get(`/tryon/result/${taskId}`)
  return response.data
}

/**
 * 删除任务
 * @param {string} taskId - 服务器端任务ID
 * @returns {Promise} 返回删除结果
 */
export async function deleteTask(taskId) {
  const response = await api.delete(`/tryon/task/${taskId}`)
  return response.data
}

/**
 * 重新提交任务（更新现有任务而非新建）
 * @param {string} taskId - 服务器端任务ID
 * @param {FormData} formData - 包含图片和参数的表单数据
 * @returns {Promise} 返回任务信息
 */
export async function resubmitTask(taskId, formData) {
  // 构建请求头
  const headers = { 'Content-Type': 'multipart/form-data' }

  // 检查配置方式
  const configMethod = localStorage.getItem('configMethod')

  // 如果是手动输入模式，添加API Key到请求头
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

  // 添加模型参数到formData
  const vlModel = localStorage.getItem('vlModel') || 'qwen3-vl-plus'
  const imgGenModel = localStorage.getItem('imgGenModel') || 'wan2.6-image'
  formData.append('vl_model', vlModel)
  formData.append('img_gen_model', imgGenModel)

  const response = await api.put(`/tryon/resubmit/${taskId}`, formData, { headers })
  return response.data
}

export default api
