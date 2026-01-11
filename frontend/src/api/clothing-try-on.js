import { createTryOnApi } from './common'

// 创建服装试穿API实例
const clothingApi = createTryOnApi('clothing-try-on')

// 导出所有方法
export const submitClothingTryOnTask = clothingApi.submitTask
export const getClothingTaskStatus = clothingApi.getTaskStatus
export const getClothingTaskResult = clothingApi.getTaskResult
export const deleteClothingTask = clothingApi.deleteTask
export const resubmitClothingTask = clothingApi.resubmitTask

export default clothingApi
