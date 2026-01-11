<template>
  <div class="tryon-page">
    <div class="page-header">
      <h1>{{ $t('tryon.title') }}</h1>
      <p>{{ $t('tryon.subtitle') }}</p>
      <div class="author-info">
        <span>{{ $t('common.author') }}：Double童发发</span>
        <a href="https://space.bilibili.com/323109608" target="_blank" rel="noopener">
          <el-icon><VideoCamera /></el-icon>
          {{ $t('common.bilibiliPage') }}
        </a>
      </div>
    </div>

    <!-- 整合的主面板 -->
    <div class="main-panel">
      <!-- 左侧任务栏 -->
      <div class="panel-sidebar">
        <TaskSidebar
          :tasks="taskList"
          :active-task-id="activeTaskId"
          @new-task="handleNewTask"
          @select-task="handleSelectTask"
          @remove-task="handleRemoveTask"
        />
      </div>

      <!-- 分隔线 -->
      <div class="panel-divider"></div>

      <!-- 右侧内容区 -->
      <div class="panel-content">
        <!-- 空状态提示 -->
        <div v-if="taskList.length === 0" class="empty-state">
          <el-empty :description="$t('tryon.emptyStateDesc')">
            <template #image>
              <el-icon class="empty-icon"><DocumentAdd /></el-icon>
            </template>
          </el-empty>
        </div>

        <!-- 上传表单 -->
        <div class="upload-area" v-if="showUploadForm">
          <!-- 使用提示 - 饰品试戴 -->
          <el-alert
            v-if="currentTaskType === 'accessory'"
            class="usage-tips"
            type="info"
            :closable="false"
          >
            <template #title>
              <div class="tips-title">
                <el-icon><InfoFilled /></el-icon>
                <span>{{ $t('tryon.usageGuide') }}</span>
              </div>
            </template>
            <div class="tips-content">
              <p><strong>{{ $t('tryon.supportedTypes') }}：</strong>{{ $t('tryon.supportedTypesDesc') }}</p>
              <p><strong>{{ $t('tryon.accessoryRequirement') }}：</strong>{{ $t('tryon.accessoryRequirementDesc') }}</p>
              <p><strong>{{ $t('tryon.personRequirement') }}：</strong>{{ $t('tryon.personRequirementDesc') }}</p>
            </div>
          </el-alert>

          <!-- 使用提示 - 服装穿戴 -->
          <el-alert
            v-if="currentTaskType === 'clothing'"
            class="usage-tips"
            type="info"
            :closable="false"
          >
            <template #title>
              <div class="tips-title">
                <el-icon><InfoFilled /></el-icon>
                <span>{{ $t('clothingTryon.usageGuide') }}</span>
              </div>
            </template>
            <div class="tips-content">
              <p><strong>{{ $t('clothingTryon.supportedTypes') }}：</strong>{{ $t('clothingTryon.supportedTypesDesc') }}</p>
              <p><strong>{{ $t('clothingTryon.clothingRequirement') }}：</strong>{{ $t('clothingTryon.clothingRequirementDesc') }}</p>
              <p><strong>{{ $t('clothingTryon.personRequirement') }}：</strong>{{ $t('clothingTryon.personRequirementDesc') }}</p>
            </div>
          </el-alert>

          <!-- 饰品试戴上传区域 -->
          <div v-if="currentTaskType === 'accessory'" class="upload-section">
            <div class="upload-item">
              <h3>{{ $t('tryon.uploadAccessory') }}</h3>
              <ImageUploader v-model="jewelryImage" :label="$t('tryon.uploadAccessory')" />
              <div class="upload-hint">
                <el-icon><Warning /></el-icon>
                <span>{{ $t('tryon.accessoryHint') }}</span>
              </div>
            </div>
            <div class="upload-item">
              <h3>{{ $t('tryon.uploadPerson') }}</h3>
              <ImageUploader v-model="personImage" :label="$t('tryon.uploadPerson')" />
              <div class="upload-hint">
                <el-icon><Warning /></el-icon>
                <span>{{ $t('tryon.personHint') }}</span>
              </div>
            </div>
          </div>

          <!-- 服装穿戴上传区域 -->
          <div v-if="currentTaskType === 'clothing'" class="upload-section">
            <div class="upload-item">
              <h3>{{ $t('clothingTryon.uploadClothing') }}</h3>
              <ImageUploader v-model="clothingImage" :label="$t('clothingTryon.uploadClothing')" />
              <div class="upload-hint">
                <el-icon><Warning /></el-icon>
                <span>{{ $t('clothingTryon.clothingHint') }}</span>
              </div>
            </div>
            <div class="upload-item">
              <h3>{{ $t('clothingTryon.uploadPerson') }}</h3>
              <ImageUploader v-model="personImage" :label="$t('clothingTryon.uploadPerson')" />
              <div class="upload-hint">
                <el-icon><Warning /></el-icon>
                <span>{{ $t('clothingTryon.personHint') }}</span>
              </div>
            </div>
          </div>

          <div class="submit-section">
            <el-button
              type="primary"
              size="large"
              :disabled="!canSubmit"
              @click="handleSubmit"
            >
              {{ currentTaskType === 'accessory' ? $t('tryon.startTryon') : $t('clothingTryon.startTryon') }}
            </el-button>
          </div>

          <!-- 任务状态显示（在上传表单内部） -->
          <div v-if="activeTask && activeTask.status === 'processing'" class="status-area">
            <div class="status-content">
              <el-icon class="is-loading status-icon"><Loading /></el-icon>
              <div class="status-text">{{ activeTask.messageKey ? $t(activeTask.messageKey) : activeTask.message }}</div>
            </div>
          </div>
        </div>

        <!-- 结果显示 -->
        <ResultDisplay
          v-if="activeTask && activeTask.status === 'completed' && activeTask.result"
          :result-image-url="activeTask.result.resultImageUrl"
          :task-type="activeTask.taskType"
          :person-image-url="activeTask.result.personImageUrl"
          :jewelry-type="activeTask.result.jewelryType"
          :person-position="activeTask.result.personPosition"
          :original-jewelry-url="activeTask.result.accessoryImageUrl || activeTask.originalImages?.jewelryImageUrl"
          :original-clothing-url="activeTask.result.clothingImageUrl || activeTask.originalImages?.clothingImageUrl"
          :original-person-url="activeTask.result.serverPersonImageUrl || activeTask.originalImages?.personImageUrl"
          @retry="handleRetry"
        />

        <!-- 设置提示 -->
        <div v-if="activeTask && activeTask.status === 'completed' && activeTask.result" class="settings-tip">
          <span>{{ $t('tryon.settingsTip') }}</span>
          <router-link to="/settings?tab=features">{{ $t('tryon.settingsLink') }}</router-link>
          <span>{{ $t('tryon.settingsTipEnd') }}</span>
        </div>

        <!-- 错误显示 -->
        <div v-if="activeTask && activeTask.status === 'failed'" class="error-area">
          <el-result icon="error" :title="$t('tryon.generateFailed')" :sub-title="activeTask.message">
            <template #extra>
              <span class="error-hint">{{ $t('tryon.reuploadHint') }}</span>
            </template>
          </el-result>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoCamera, InfoFilled, Warning, DocumentAdd } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import ImageUploader from '../components/ImageUploader.vue'
import ResultDisplay from '../components/ResultDisplay.vue'
import TaskSidebar from '../components/TaskSidebar.vue'
import { submitTryOnTask, getTaskStatus, getTaskResult, deleteTask, resubmitTask } from '../api/accessory-try-on'
import { submitClothingTryOnTask, getClothingTaskStatus, getClothingTaskResult, deleteClothingTask, resubmitClothingTask } from '../api/clothing-try-on'
import { saveTaskImages, loadTaskImages, deleteTaskImages, cleanupOrphanImages } from '../utils/imageStorage'

const { t } = useI18n()

// 轮询配置常量
const POLLING_MAX_ATTEMPTS = 120  // 最大轮询次数
const POLLING_INTERVAL_MS = 2500  // 轮询间隔（毫秒）

// 表单数据
const jewelryImage = ref(null)
const clothingImage = ref(null)
const personImage = ref(null)
const jewelryType = ref('')
const clothingType = ref('')
const personPosition = ref('')
const useVlModel = ref(true)

// 功能选择（默认为饰品试戴）
const selectedFeature = ref('accessory')

// 任务列表
const taskList = ref([])
const activeTaskId = ref('')

// 任务列表持久化到 localStorage
const TASK_LIST_KEY = 'tryon_tasks'
const ACTIVE_TASK_ID_KEY = 'tryon_active_task_id'

// 监听任务列表变化，保存到 localStorage
watch(taskList, async (newTaskList) => {
  try {
    // 序列化任务列表，排除无法序列化的 File 对象和 Blob URL
    const serializableTasks = newTaskList.map(task => ({
      id: task.id,
      taskNumber: task.taskNumber,
      taskType: task.taskType,  // 保存任务类型
      status: task.status,
      messageKey: task.messageKey,
      messageParams: task.messageParams,
      result: task.result,
      serverTaskId: task.serverTaskId
    }))
    localStorage.setItem(TASK_LIST_KEY, JSON.stringify(serializableTasks))

    // 同步保存图片到 IndexedDB（仅保存有 originalImages 的任务）
    for (const task of newTaskList) {
      if (task.originalImages) {
        await saveTaskImages(task.id, {
          jewelryImage: task.originalImages.jewelryImage,
          clothingImage: task.originalImages.clothingImage,
          personImage: task.originalImages.personImage
        })
      }
    }
  } catch (error) {
    console.error('保存任务列表失败:', error)
  }
}, { deep: true })

// 监听活动任务ID变化
watch(activeTaskId, (newActiveTaskId) => {
  try {
    localStorage.setItem(ACTIVE_TASK_ID_KEY, newActiveTaskId)
  } catch (error) {
    console.error('保存活动任务ID失败:', error)
  }
})

// 监听表单图片变化，实时同步到当前任务并持久化到 IndexedDB
// 解决：用户上传图片后切换页面，图片丢失的问题
watch([jewelryImage, clothingImage, personImage], async ([newJewelry, newClothing, newPerson]) => {
  const task = activeTask.value
  if (!task) return

  // 只有当有图片上传时才更新
  if (!newJewelry && !newClothing && !newPerson) return

  // 初始化 originalImages（如果不存在）
  if (!task.originalImages) {
    task.originalImages = {}
  }

  // 同步图片到当前任务
  if (task.taskType === 'accessory') {
    if (newJewelry) {
      task.originalImages.jewelryImage = newJewelry
      task.originalImages.jewelryImageUrl = URL.createObjectURL(newJewelry)
    }
  } else {
    if (newClothing) {
      task.originalImages.clothingImage = newClothing
      task.originalImages.clothingImageUrl = URL.createObjectURL(newClothing)
    }
  }

  if (newPerson) {
    task.originalImages.personImage = newPerson
    task.originalImages.personImageUrl = URL.createObjectURL(newPerson)
  }

  // 立即保存到 IndexedDB
  await saveTaskImages(task.id, {
    jewelryImage: task.originalImages.jewelryImage,
    clothingImage: task.originalImages.clothingImage,
    personImage: task.originalImages.personImage
  })
}, { deep: true })

// 是否可以提交
const canSubmit = computed(() => {
  if (currentTaskType.value === 'accessory') {
    return jewelryImage.value && personImage.value
  } else {
    return clothingImage.value && personImage.value
  }
})

// 当前任务类型（优先使用活动任务的类型，否则使用选择的功能类型）
const currentTaskType = computed(() => {
  if (activeTask.value && activeTask.value.taskType) {
    return activeTask.value.taskType
  }
  return selectedFeature.value
})

// 当前选中的任务
const activeTask = computed(() => {
  return taskList.value.find(t => t.id === activeTaskId.value)
})

// 是否显示上传表单（只有当存在活动任务时才显示）
const showUploadForm = computed(() => {
  return activeTaskId.value !== ''
})

// 提交任务
async function handleSubmit() {
  const currentTask = activeTask.value

  // 判断是否是更新等待上传的任务
  const isUpdateWaitingTask = currentTask && currentTask.status === 'waiting_upload'

  // 判断是否是在现有任务上重新提交（任务已完成或失败，且有serverTaskId）
  const isResubmit = currentTask &&
    currentTask.serverTaskId &&
    (currentTask.status === 'completed' || currentTask.status === 'failed')

  if (isUpdateWaitingTask) {
    // 更新等待上传的任务
    await handleUpdateWaitingTask(currentTask)
  } else if (isResubmit) {
    // 重新提交现有任务
    await handleResubmitExistingTask(currentTask)
  } else {
    // 创建新任务
    await handleCreateNewTask()
  }
}

// 更新等待上传的任务（将等待上传状态的任务更新为处理中）
async function handleUpdateWaitingTask(task) {
  const taskId = task.id
  const taskType = task.taskType || selectedFeature.value

  // 根据任务类型获取对应的图片
  const mainImage = taskType === 'accessory' ? jewelryImage.value : clothingImage.value
  const mainImageUrl = URL.createObjectURL(mainImage)
  const personImageUrl = URL.createObjectURL(personImage.value)

  // 更新任务的原始图片信息
  const originalImages = {
    personImage: personImage.value,
    personImageUrl: personImageUrl,
    personPosition: personPosition.value,
    useVlModel: useVlModel.value
  }

  if (taskType === 'accessory') {
    originalImages.jewelryImage = mainImage
    originalImages.jewelryImageUrl = mainImageUrl
    originalImages.jewelryType = jewelryType.value
  } else {
    originalImages.clothingImage = mainImage
    originalImages.clothingImageUrl = mainImageUrl
    originalImages.clothingType = clothingType.value
  }

  updateTask(taskId, {
    status: 'pending',
    messageKey: taskType === 'accessory' ? 'tryon.preparing' : 'clothingTryon.preparing',
    result: null,
    originalImages
  })

  try {
    // 构建表单数据
    const formData = new FormData()
    formData.append('person_image', personImage.value)
    formData.append('use_vl_model', useVlModel.value)

    if (taskType === 'accessory') {
      formData.append('accessory_image', mainImage)
      if (jewelryType.value) {
        formData.append('accessory_type', jewelryType.value)
      }
    } else {
      formData.append('clothing_image', mainImage)
      if (clothingType.value) {
        formData.append('clothing_type', clothingType.value)
      }
    }

    if (personPosition.value) {
      formData.append('person_position', personPosition.value)
    }

    // 更新任务状态
    updateTask(taskId, { status: 'processing', messageKey: taskType === 'accessory' ? 'tryon.uploading' : 'clothingTryon.uploading' })

    // 根据任务类型提交任务
    const submitRes = taskType === 'accessory'
      ? await submitTryOnTask(formData)
      : await submitClothingTryOnTask(formData)
    updateTask(taskId, { serverTaskId: submitRes.task_id })

    // 如果后端因超出上限删除了旧任务，同步更新前端列表
    if (submitRes.deleted_task_id) {
      const deletedIndex = taskList.value.findIndex(
        t => t.serverTaskId === submitRes.deleted_task_id
      )
      if (deletedIndex > -1) {
        const deletedTask = taskList.value[deletedIndex]
        taskList.value.splice(deletedIndex, 1)
        ElMessage({
          message: t('messages.taskLimitReached', { name: deletedTask.name }),
          type: 'warning',
          duration: 4000,
          showClose: true,
          offset: 60
        })
      }
    }

    // 开始轮询
    pollTaskStatus(taskId, submitRes.task_id)

  } catch (error) {
    updateTask(taskId, { status: 'failed', messageKey: 'messages.taskSubmitFailed', messageParams: error.message })
    ElMessage({
      message: t('messages.taskSubmitFailed') + ': ' + (error.message || t('messages.networkError')),
      type: 'error',
      duration: 3000,
      showClose: true,
      offset: 60
    })
  }
}

// 重新提交现有任务（更新任务状态而非新建）
async function handleResubmitExistingTask(task) {
  const taskId = task.id
  const serverTaskId = task.serverTaskId
  const taskType = task.taskType || selectedFeature.value

  // 清理旧的本地URL
  if (task.originalImages) {
    revokeObjectUrls(task.originalImages)
  }

  // 根据任务类型获取对应的图片
  const mainImage = taskType === 'accessory' ? jewelryImage.value : clothingImage.value
  const mainImageUrl = URL.createObjectURL(mainImage)
  const personImageUrl = URL.createObjectURL(personImage.value)

  // 构建原始图片信息
  const originalImages = {
    personImage: personImage.value,
    personImageUrl: personImageUrl,
    personPosition: personPosition.value,
    useVlModel: useVlModel.value
  }

  if (taskType === 'accessory') {
    originalImages.jewelryImage = mainImage
    originalImages.jewelryImageUrl = mainImageUrl
    originalImages.jewelryType = jewelryType.value
  } else {
    originalImages.clothingImage = mainImage
    originalImages.clothingImageUrl = mainImageUrl
    originalImages.clothingType = clothingType.value
  }

  updateTask(taskId, {
    status: 'pending',
    messageKey: taskType === 'accessory' ? 'tryon.preparing' : 'clothingTryon.preparing',
    result: null,
    originalImages
  })

  try {
    const formData = new FormData()
    formData.append('person_image', personImage.value)
    formData.append('use_vl_model', useVlModel.value)

    if (taskType === 'accessory') {
      formData.append('accessory_image', mainImage)
      if (jewelryType.value) {
        formData.append('accessory_type', jewelryType.value)
      }
    } else {
      formData.append('clothing_image', mainImage)
      if (clothingType.value) {
        formData.append('clothing_type', clothingType.value)
      }
    }

    if (personPosition.value) {
      formData.append('person_position', personPosition.value)
    }

    updateTask(taskId, { status: 'processing', messageKey: taskType === 'accessory' ? 'tryon.uploading' : 'clothingTryon.uploading' })

    // 根据任务类型调用不同的API
    taskType === 'accessory'
      ? await resubmitTask(serverTaskId, formData)
      : await resubmitClothingTask(serverTaskId, formData)

    pollTaskStatus(taskId, serverTaskId)

  } catch (error) {
    updateTask(taskId, { status: 'failed', messageKey: 'messages.taskSubmitFailed', messageParams: error.message })
    ElMessage({
      message: t('messages.taskSubmitFailed') + ': ' + (error.message || t('messages.networkError')),
      type: 'error',
      duration: 3000,
      showClose: true,
      offset: 60
    })
  }
}

// 创建新任务
async function handleCreateNewTask() {
  const taskNumber = taskList.value.length + 1
  const taskId = `local-${Date.now()}`
  const taskType = selectedFeature.value

  // 释放旧任务的URL
  const currentTask = activeTask.value
  if (currentTask && currentTask.originalImages) {
    revokeObjectUrls(currentTask.originalImages)
  }

  // 根据任务类型获取对应的图片
  const mainImage = taskType === 'accessory' ? jewelryImage.value : clothingImage.value
  const mainImageUrl = URL.createObjectURL(mainImage)
  const personImageUrl = URL.createObjectURL(personImage.value)

  // 构建原始图片信息
  const originalImages = {
    personImage: personImage.value,
    personImageUrl: personImageUrl,
    personPosition: personPosition.value,
    useVlModel: useVlModel.value
  }

  if (taskType === 'accessory') {
    originalImages.jewelryImage = mainImage
    originalImages.jewelryImageUrl = mainImageUrl
    originalImages.jewelryType = jewelryType.value
  } else {
    originalImages.clothingImage = mainImage
    originalImages.clothingImageUrl = mainImageUrl
    originalImages.clothingType = clothingType.value
  }

  const newTask = {
    id: taskId,
    taskNumber: taskNumber,
    taskType: taskType,
    status: 'pending',
    messageKey: taskType === 'accessory' ? 'tryon.preparing' : 'clothingTryon.preparing',
    result: null,
    serverTaskId: null,
    originalImages
  }
  taskList.value.unshift(newTask)
  activeTaskId.value = taskId

  // 保存表单数据
  const formMainImage = mainImage
  const formPersonImage = personImage.value
  const formPersonPosition = personPosition.value
  const formUseVlModel = useVlModel.value

  try {
    const formData = new FormData()
    formData.append('person_image', formPersonImage)
    formData.append('use_vl_model', formUseVlModel)

    if (taskType === 'accessory') {
      formData.append('accessory_image', formMainImage)
      if (jewelryType.value) {
        formData.append('accessory_type', jewelryType.value)
      }
    } else {
      formData.append('clothing_image', formMainImage)
      if (clothingType.value) {
        formData.append('clothing_type', clothingType.value)
      }
    }

    if (formPersonPosition) {
      formData.append('person_position', formPersonPosition)
    }

    updateTask(taskId, { status: 'processing', messageKey: taskType === 'accessory' ? 'tryon.uploading' : 'clothingTryon.uploading' })

    // 根据任务类型提交
    const submitRes = taskType === 'accessory'
      ? await submitTryOnTask(formData)
      : await submitClothingTryOnTask(formData)
    updateTask(taskId, { serverTaskId: submitRes.task_id })

    // 如果后端因超出上限删除了旧任务，同步更新前端列表
    if (submitRes.deleted_task_id) {
      const deletedIndex = taskList.value.findIndex(
        t => t.serverTaskId === submitRes.deleted_task_id
      )
      if (deletedIndex > -1) {
        const deletedTask = taskList.value[deletedIndex]
        taskList.value.splice(deletedIndex, 1)
        ElMessage({
          message: t('messages.taskLimitReached', { name: deletedTask.name }),
          type: 'warning',
          duration: 4000,
          showClose: true,
          offset: 60
        })
      }
    }

    // 开始轮询
    pollTaskStatus(taskId, submitRes.task_id)

  } catch (error) {
    updateTask(taskId, { status: 'failed', messageKey: 'messages.taskSubmitFailed', messageParams: error.message })
    ElMessage({
      message: t('messages.taskSubmitFailed') + ': ' + (error.message || t('messages.networkError')),
      type: 'error',
      duration: 3000,
      showClose: true,
      offset: 60
    })
  }
}

// 更新任务
function updateTask(taskId, updates) {
  const task = taskList.value.find(t => t.id === taskId)
  if (task) {
    Object.assign(task, updates)
  }
}

// 轮询任务状态
async function pollTaskStatus(localTaskId, serverTaskId) {
  let attempts = 0

  // 获取任务类型
  const task = taskList.value.find(t => t.id === localTaskId)
  const taskType = task?.taskType || 'accessory'

  // 中文消息到翻译key的映射表
  const messageKeyMap = {
    '准备中...': taskType === 'accessory' ? 'tryon.preparing' : 'clothingTryon.preparing',
    '正在上传图片...': taskType === 'accessory' ? 'tryon.uploading' : 'clothingTryon.uploading',
    'VL模型分析图像中...': taskType === 'accessory' ? 'tryon.vlAnalyzing' : 'clothingTryon.vlAnalyzing',
    '试戴图像生成中...': 'tryon.generating',
    '试穿图像生成中...': 'clothingTryon.generating',
    '处理中...': taskType === 'accessory' ? 'tryon.processing' : 'clothingTryon.processing'
  }

  while (attempts < POLLING_MAX_ATTEMPTS) {
    try {
      // 根据任务类型调用不同的API
      const status = taskType === 'accessory'
        ? await getTaskStatus(serverTaskId)
        : await getClothingTaskStatus(serverTaskId)

      const messageKey = messageKeyMap[status.message] || null
      if (messageKey) {
        updateTask(localTaskId, { messageKey: messageKey })
      } else {
        updateTask(localTaskId, { message: status.message || t('tryon.processing'), messageKey: null })
      }

      if (status.status === 'completed') {
        const taskResult = taskType === 'accessory'
          ? await getTaskResult(serverTaskId)
          : await getClothingTaskResult(serverTaskId)
        const taskName = task ? `${t('tryon.task')} ${task.taskNumber}` : t('tryon.task')

        updateTask(localTaskId, {
          status: 'completed',
          messageKey: 'tryon.completed',
          result: {
            resultImageUrl: taskResult.result_image_url,
            personImageUrl: taskResult.person_image_url,
            jewelryType: taskResult.accessory_type,
            personPosition: taskResult.person_position,
            // 保存服务器端的原始图片URL（用于页面切换后恢复显示）
            accessoryImageUrl: taskResult.accessory_image_url,
            clothingImageUrl: taskResult.clothing_image_url,
            serverPersonImageUrl: taskResult.person_image_url
          }
        })
        ElMessage({
          message: t('messages.taskCompleted') + `: ${taskName}`,
          type: 'success',
          duration: 2000,
          showClose: true,
          offset: 60
        })
        return
      }

      if (status.status === 'failed') {
        updateTask(localTaskId, { status: 'failed', messageKey: 'messages.taskFailed', messageParams: status.message })
        return
      }
    } catch (error) {
      // 检查是否是 404 错误（任务在后端不存在，可能是服务重启导致）
      if (error.response && error.response.status === 404) {
        updateTask(localTaskId, {
          status: 'failed',
          messageKey: 'tryon.serviceInterrupted'
        })
        return
      }
      // 其他网络错误，继续重试
    }

    await new Promise(resolve => setTimeout(resolve, POLLING_INTERVAL_MS))
    attempts++
  }

  updateTask(localTaskId, { status: 'failed', messageKey: 'tryon.timeout' })
}

// 新建任务
function handleNewTask(taskType) {
  const taskNumber = taskList.value.length + 1
  const taskId = `local-${Date.now()}`

  const newTask = {
    id: taskId,
    taskNumber: taskNumber,
    taskType: taskType,
    status: 'waiting_upload',
    messageKey: taskType === 'accessory' ? 'tryon.waitingUpload' : 'clothingTryon.waitingUpload',
    result: null,
    serverTaskId: null,
    originalImages: null
  }

  taskList.value.unshift(newTask)
  activeTaskId.value = taskId

  // 清空表单
  jewelryImage.value = null
  clothingImage.value = null
  personImage.value = null
}

// 重新生成（在当前任务上重试，而非创建新任务）
async function handleRetry() {
  const currentTask = activeTask.value

  if (!currentTask || !currentTask.serverTaskId) {
    ElMessage({
      message: t('tryon.retryFailed'),
      type: 'warning',
      duration: 2000,
      showClose: true,
      offset: 60
    })
    return
  }

  const taskId = currentTask.id
  const serverTaskId = currentTask.serverTaskId
  const taskType = currentTask.taskType || 'accessory'

  updateTask(taskId, {
    status: 'processing',
    messageKey: taskType === 'accessory' ? 'tryon.retrying' : 'clothingTryon.retrying',
    result: null
  })

  try {
    const formData = new FormData()
    formData.append('use_vl_model', currentTask.originalImages?.useVlModel ?? true)

    if (currentTask.originalImages?.personImage) {
      formData.append('person_image', currentTask.originalImages.personImage)
    }
    if (currentTask.originalImages?.personPosition) {
      formData.append('person_position', currentTask.originalImages.personPosition)
    }

    if (taskType === 'accessory') {
      if (currentTask.originalImages?.jewelryImage) {
        formData.append('accessory_image', currentTask.originalImages.jewelryImage)
      }
      if (currentTask.originalImages?.jewelryType) {
        formData.append('accessory_type', currentTask.originalImages.jewelryType)
      }
      await resubmitTask(serverTaskId, formData)
    } else {
      if (currentTask.originalImages?.clothingImage) {
        formData.append('clothing_image', currentTask.originalImages.clothingImage)
      }
      if (currentTask.originalImages?.clothingType) {
        formData.append('clothing_type', currentTask.originalImages.clothingType)
      }
      await resubmitClothingTask(serverTaskId, formData)
    }

    pollTaskStatus(taskId, serverTaskId)

  } catch (error) {
    updateTask(taskId, {
      status: 'failed',
      messageKey: 'messages.taskSubmitFailed',
      messageParams: error.message
    })
    ElMessage({
      message: t('tryon.retryError') + ': ' + (error.message || t('messages.networkError')),
      type: 'error',
      duration: 3000,
      showClose: true,
      offset: 60
    })
  }
}

// 选择任务
function handleSelectTask(taskId) {
  activeTaskId.value = taskId

  const task = taskList.value.find(t => t.id === taskId)
  if (task && task.originalImages) {
    // 根据任务类型恢复对应的图片
    if (task.taskType === 'accessory') {
      jewelryImage.value = task.originalImages.jewelryImage
      clothingImage.value = null
    } else {
      clothingImage.value = task.originalImages.clothingImage
      jewelryImage.value = null
    }
    personImage.value = task.originalImages.personImage
  } else {
    jewelryImage.value = null
    clothingImage.value = null
    personImage.value = null
  }
}

// 删除任务
async function handleRemoveTask(taskId) {
  const task = taskList.value.find(t => t.id === taskId)
  const taskType = task?.taskType || 'accessory'

  if (task && task.serverTaskId) {
    try {
      taskType === 'accessory'
        ? await deleteTask(task.serverTaskId)
        : await deleteClothingTask(task.serverTaskId)
    } catch (error) {
      console.warn('后端删除任务失败:', error)
    }
  }

  const index = taskList.value.findIndex(t => t.id === taskId)
  if (index > -1) {
    if (taskList.value[index].originalImages) {
      revokeObjectUrls(taskList.value[index].originalImages)
    }
    taskList.value.splice(index, 1)
  }

  // 删除 IndexedDB 中的图片数据
  await deleteTaskImages(taskId)

  if (activeTaskId.value === taskId) {
    activeTaskId.value = taskList.value[0]?.id || ''
  }
}

function revokeObjectUrls(originalImages) {
  try {
    if (originalImages.jewelryImageUrl) {
      URL.revokeObjectURL(originalImages.jewelryImageUrl)
    }
    if (originalImages.clothingImageUrl) {
      URL.revokeObjectURL(originalImages.clothingImageUrl)
    }
    if (originalImages.personImageUrl) {
      URL.revokeObjectURL(originalImages.personImageUrl)
    }
  } catch (err) {
    console.warn('释放本地图片URL失败', err)
  }
}

/**
 * 验证任务列表中的任务是否在后端存在
 * 对于后端不存在的任务，标记为失败状态
 */
async function validateTasks(tasks) {
  const validationPromises = tasks.map(async (task) => {
    // 情况1：状态为 processing 或 pending，但没有 serverTaskId
    // 说明任务在提交过程中中断（服务重启），直接标记为失败
    if ((task.status === 'processing' || task.status === 'pending') && !task.serverTaskId) {
      return {
        task: {
          ...task,
          status: 'failed',
          messageKey: 'tryon.serviceInterrupted'
        },
        valid: true,
        needsPoll: false
      }
    }

    // 情况2：有 serverTaskId 且状态为 processing，验证后端任务是否存在
    if (task.serverTaskId && task.status === 'processing') {
      try {
        // 根据任务类型调用对应的API
        const taskType = task.taskType || 'accessory'
        taskType === 'accessory'
          ? await getTaskStatus(task.serverTaskId)
          : await getClothingTaskStatus(task.serverTaskId)
        // 任务存在，返回原任务继续轮询
        return { task, valid: true, needsPoll: true }
      } catch (error) {
        if (error.response && error.response.status === 404) {
          // 任务在后端不存在，标记为失败
          return {
            task: {
              ...task,
              status: 'failed',
              messageKey: 'tryon.serviceInterrupted'
            },
            valid: true,
            needsPoll: false
          }
        }
        // 其他错误（如网络问题），保持原状态继续轮询
        return { task, valid: true, needsPoll: true }
      }
    }

    // 其他状态的任务直接保留
    return { task, valid: true, needsPoll: false }
  })

  const results = await Promise.all(validationPromises)

  // 更新任务列表
  const validatedTasks = results.map(r => r.task)

  // 返回需要继续轮询的任务
  const tasksNeedingPoll = results
    .filter(r => r.needsPoll)
    .map(r => r.task)

  return { validatedTasks, tasksNeedingPoll }
}

// 从localStorage加载功能设置
onMounted(async () => {
  // 加载VL模型增强设置
  const savedUseVlModel = localStorage.getItem('useVlModel')
  if (savedUseVlModel !== null) {
    useVlModel.value = savedUseVlModel === 'true'
  }

  // 加载默认饰品类型
  const savedJewelryType = localStorage.getItem('defaultJewelryType')
  if (savedJewelryType) {
    jewelryType.value = savedJewelryType
  }

  // 加载默认佩戴位置
  const savedPersonPosition = localStorage.getItem('defaultPersonPosition')
  if (savedPersonPosition) {
    personPosition.value = savedPersonPosition
  }

  // 从 localStorage 恢复任务列表
  try {
    const savedTasks = localStorage.getItem(TASK_LIST_KEY)
    if (savedTasks) {
      const tasks = JSON.parse(savedTasks)

      // 验证任务有效性，清理后端不存在的任务
      const { validatedTasks, tasksNeedingPoll } = await validateTasks(tasks)

      // 从 IndexedDB 恢复每个任务的图片数据
      for (const task of validatedTasks) {
        const images = await loadTaskImages(task.id)
        if (images) {
          // 重建 originalImages 对象
          task.originalImages = {
            jewelryImage: images.jewelryImage,
            clothingImage: images.clothingImage,
            personImage: images.personImage,
            // 重新生成预览 URL
            jewelryImageUrl: images.jewelryImage ? URL.createObjectURL(images.jewelryImage) : null,
            clothingImageUrl: images.clothingImage ? URL.createObjectURL(images.clothingImage) : null,
            personImageUrl: images.personImage ? URL.createObjectURL(images.personImage) : null
          }
        }
      }

      taskList.value = validatedTasks

      // 清理 IndexedDB 中不存在于任务列表的孤立图片数据
      const validTaskIds = validatedTasks.map(t => t.id)
      await cleanupOrphanImages(validTaskIds)

      // 恢复处理中的任务，继续轮询状态
      tasksNeedingPoll.forEach(task => {
        console.log(`恢复任务轮询: ${task.taskNumber} (${task.serverTaskId})`)
        pollTaskStatus(task.id, task.serverTaskId)
      })
    }
  } catch (error) {
    console.error('恢复任务列表失败:', error)
  }

  // 恢复活动任务ID，并恢复对应的图片状态
  try {
    const savedActiveTaskId = localStorage.getItem(ACTIVE_TASK_ID_KEY)
    if (savedActiveTaskId) {
      activeTaskId.value = savedActiveTaskId

      // 恢复对应任务的图片状态到表单
      const task = taskList.value.find(t => t.id === savedActiveTaskId)
      if (task && task.originalImages) {
        if (task.taskType === 'accessory') {
          jewelryImage.value = task.originalImages.jewelryImage
          clothingImage.value = null
        } else {
          clothingImage.value = task.originalImages.clothingImage
          jewelryImage.value = null
        }
        personImage.value = task.originalImages.personImage
      }
    }
  } catch (error) {
    console.error('恢复活动任务ID失败:', error)
  }
})
</script>

<style scoped>
.tryon-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 24px;
  color: white;
}

.page-header h1 {
  font-size: 32px;
  margin-bottom: 8px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.page-header p {
  font-size: 14px;
  opacity: 0.9;
}

.author-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 12px;
  font-size: 13px;
  opacity: 0.85;
}

.author-info a {
  display: flex;
  align-items: center;
  gap: 4px;
  color: white;
  text-decoration: none;
  padding: 4px 12px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  transition: all 0.3s;
}

.author-info a:hover {
  background: rgba(255, 255, 255, 0.25);
}

.main-panel {
  display: flex;
  background: white;
  border-radius: 20px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  min-height: 500px;
}

.panel-sidebar {
  width: 280px;
  flex-shrink: 0;
  background: #fafbfc;
}

.panel-sidebar :deep(.task-sidebar) {
  background: transparent;
  box-shadow: none;
  border-radius: 0;
  height: 100%;
}

.panel-divider {
  width: 1px;
  background: linear-gradient(to bottom, transparent, #e4e7ed, transparent);
}

.panel-content {
  flex: 1;
  min-width: 0;
  padding: 24px;
}

/* 空状态提示样式 */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.empty-icon {
  font-size: 80px;
  color: #c0c4cc;
}

.usage-tips {
  margin-bottom: 24px;
  border-radius: 8px;
}

.tips-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
}

.tips-content {
  margin-top: 8px;
  line-height: 1.8;
}

.tips-content p {
  margin: 8px 0;
  font-size: 14px;
}

.tips-content strong {
  color: #409eff;
}

.upload-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.upload-item h3 {
  margin-bottom: 12px;
  color: #303133;
  font-size: 16px;
}

.upload-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 13px;
  color: #e6a23c;
}

.upload-hint .el-icon {
  font-size: 14px;
}

.submit-section {
  text-align: center;
  margin-bottom: 16px;
}

.settings-tip {
  text-align: center;
  margin-top: 16px;
  padding: 12px;
  font-size: 14px;
  color: #909399;
}

.settings-tip a {
  color: #409eff;
  text-decoration: none;
  margin: 0 4px;
}

.settings-tip a:hover {
  text-decoration: underline;
}

.status-area {
  margin-bottom: 16px;
}

.status-content {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  gap: 16px;
}

.status-icon {
  font-size: 32px;
  color: #409eff;
}

.status-text {
  font-size: 16px;
  color: #606266;
}

.error-area {
  padding: 20px 0;
}

.error-hint {
  color: #909399;
  font-size: 14px;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.is-loading {
  animation: rotate 1s linear infinite;
}

@media (max-width: 768px) {
  .main-panel {
    flex-direction: column;
  }

  .panel-sidebar {
    width: 100%;
  }

  .panel-divider {
    width: 100%;
    height: 1px;
  }

  .upload-section {
    grid-template-columns: 1fr;
  }
}
</style>

<!-- 深色模式适配 -->
<style>
html.dark .main-panel {
  background: #2d3748;
}

html.dark .panel-sidebar {
  background: #1f2937;
}

html.dark .panel-content {
  background: #2d3748;
}

html.dark .empty-icon {
  color: #6b7280;
}

html.dark .upload-item h3 {
  color: #f5f5f5;
}

html.dark .settings-tip {
  color: #d1d5db;
}

html.dark .status-text {
  color: #e5e7eb;
}

html.dark .error-hint {
  color: #d1d5db;
}
</style>
