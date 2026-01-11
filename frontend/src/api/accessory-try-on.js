import { createTryOnApi } from './common'

// 创建饰品试戴API实例
const accessoryApi = createTryOnApi('accessory-try-on')

// 导出所有方法
export const submitTryOnTask = accessoryApi.submitTask
export const getTaskStatus = accessoryApi.getTaskStatus
export const getTaskResult = accessoryApi.getTaskResult
export const deleteTask = accessoryApi.deleteTask
export const resubmitTask = accessoryApi.resubmitTask

export default accessoryApi
