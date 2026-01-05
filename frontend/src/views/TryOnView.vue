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

    <!-- 功能选择器 -->
    <div class="feature-selector">
      <el-radio-group v-model="selectedFeature" size="large">
        <el-radio-button value="accessory">
          {{ $t('features.accessoryTryon') }}
        </el-radio-button>
        <el-tooltip :content="$t('features.comingSoon')" placement="top">
          <el-radio-button value="clothing" disabled>
            {{ $t('features.clothingTryon') }}
          </el-radio-button>
        </el-tooltip>
      </el-radio-group>
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
            <el-button type="primary" @click="handleNewTask">
              <el-icon><Plus /></el-icon>
              {{ $t('taskSidebar.newTask') }}
            </el-button>
          </el-empty>
        </div>

        <!-- 上传表单 -->
        <div class="upload-area" v-if="showUploadForm">
          <!-- 使用提示 -->
          <el-alert
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

          <div class="upload-section">
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

          <div class="submit-section">
            <el-button
              type="primary"
              size="large"
              :disabled="!canSubmit"
              @click="handleSubmit"
            >
              {{ $t('tryon.startTryon') }}
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
          :person-image-url="activeTask.result.personImageUrl"
          :jewelry-type="activeTask.result.jewelryType"
          :person-position="activeTask.result.personPosition"
          :original-jewelry-url="activeTask.result.accessoryImageUrl || activeTask.originalImages?.jewelryImageUrl"
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
import { VideoCamera, InfoFilled, Warning, DocumentAdd, Plus } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import ImageUploader from '../components/ImageUploader.vue'
import ResultDisplay from '../components/ResultDisplay.vue'
import TaskSidebar from '../components/TaskSidebar.vue'
import { submitTryOnTask, getTaskStatus, getTaskResult, deleteTask, resubmitTask } from '../api/tryon'

const { t } = useI18n()

// 表单数据
const jewelryImage = ref(null)
const personImage = ref(null)
const jewelryType = ref('')
const personPosition = ref('')
const useVlModel = ref(true)

// 功能选择（默认为饰品试戴）
const selectedFeature = ref('accessory')

// 任务列表
const taskList = ref([])
const activeTaskId = ref('')

// 任务列表持久化到 localStorage
const TASK_LIST_KEY = 'accessory_tryon_tasks'
const ACTIVE_TASK_ID_KEY = 'accessory_tryon_active_task_id'

// 监听任务列表变化，保存到 localStorage
watch(taskList, (newTaskList) => {
  try {
    // 序列化任务列表，排除无法序列化的 File 对象和 Blob URL
    const serializableTasks = newTaskList.map(task => ({
      id: task.id,
      taskNumber: task.taskNumber,  // 保存任务编号，显示时动态翻译
      status: task.status,
      messageKey: task.messageKey,  // 保存翻译key，显示时动态翻译
      messageParams: task.messageParams,  // 保存额外的消息参数
      result: task.result,
      serverTaskId: task.serverTaskId
      // 注意：不保存 originalImages，因为包含 File 对象和 Blob URL
    }))
    localStorage.setItem(TASK_LIST_KEY, JSON.stringify(serializableTasks))
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

// 是否可以提交
const canSubmit = computed(() => {
  return jewelryImage.value && personImage.value
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

  // 保存原始图片信息（用于重新生成）
  const jewelryImageUrl = URL.createObjectURL(jewelryImage.value)
  const personImageUrl = URL.createObjectURL(personImage.value)

  // 更新任务的原始图片信息
  updateTask(taskId, {
    status: 'pending',
    messageKey: 'tryon.preparing',
    result: null,
    originalImages: {
      jewelryImage: jewelryImage.value,
      personImage: personImage.value,
      jewelryImageUrl: jewelryImageUrl,
      personImageUrl: personImageUrl,
      jewelryType: jewelryType.value,
      personPosition: personPosition.value,
      useVlModel: useVlModel.value
    }
  })

  try {
    // 构建表单数据
    const formData = new FormData()
    formData.append('accessory_image', jewelryImage.value)
    formData.append('person_image', personImage.value)
    formData.append('use_vl_model', useVlModel.value)
    if (jewelryType.value) {
      formData.append('accessory_type', jewelryType.value)
    }
    if (personPosition.value) {
      formData.append('person_position', personPosition.value)
    }

    // 更新任务状态
    updateTask(taskId, { status: 'processing', messageKey: 'tryon.uploading' })

    // 提交任务
    const submitRes = await submitTryOnTask(formData)
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

  // 清理旧的本地URL，避免重复占用内存
  if (task.originalImages) {
    revokeObjectUrls(task.originalImages)
  }

  // 保存原始图片信息（用于重新生成）
  const jewelryImageUrl = URL.createObjectURL(jewelryImage.value)
  const personImageUrl = URL.createObjectURL(personImage.value)

  // 更新任务的原始图片信息
  updateTask(taskId, {
    status: 'pending',
    messageKey: 'tryon.preparing',
    result: null,
    originalImages: {
      jewelryImage: jewelryImage.value,
      personImage: personImage.value,
      jewelryImageUrl: jewelryImageUrl,
      personImageUrl: personImageUrl,
      jewelryType: jewelryType.value,
      personPosition: personPosition.value,
      useVlModel: useVlModel.value
    }
  })

  try {
    // 构建表单数据
    const formData = new FormData()
    formData.append('accessory_image', jewelryImage.value)
    formData.append('person_image', personImage.value)
    formData.append('use_vl_model', useVlModel.value)
    if (jewelryType.value) {
      formData.append('accessory_type', jewelryType.value)
    }
    if (personPosition.value) {
      formData.append('person_position', personPosition.value)
    }

    // 更新任务状态
    updateTask(taskId, { status: 'processing', messageKey: 'tryon.uploading' })

    // 调用重新提交API
    await resubmitTask(serverTaskId, formData)

    // 开始轮询（使用原有的serverTaskId）
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
  // 创建新任务，编号基于当前任务列表数量 + 1
  const taskNumber = taskList.value.length + 1
  const taskId = `local-${Date.now()}`  // 使用时间戳作为唯一ID

  // 如果当前有活跃任务且缓存了原始图片，先释放对应的URL
  const currentTask = activeTask.value
  if (currentTask && currentTask.originalImages) {
    revokeObjectUrls(currentTask.originalImages)
  }

  // 保存原始图片信息（用于重新生成）
  const jewelryImageUrl = URL.createObjectURL(jewelryImage.value)
  const personImageUrl = URL.createObjectURL(personImage.value)

  const newTask = {
    id: taskId,
    taskNumber: taskNumber,  // 保存任务编号，在显示时动态翻译
    status: 'pending',
    messageKey: 'tryon.preparing',  // 保存翻译key，在显示时动态翻译
    result: null,
    serverTaskId: null,
    // 保存原始图片信息
    originalImages: {
      jewelryImage: jewelryImage.value,
      personImage: personImage.value,
      jewelryImageUrl: jewelryImageUrl,
      personImageUrl: personImageUrl,
      jewelryType: jewelryType.value,
      personPosition: personPosition.value,
      useVlModel: useVlModel.value
    }
  }
  taskList.value.unshift(newTask)
  activeTaskId.value = taskId

  // 保存表单数据
  const formJewelryImage = jewelryImage.value
  const formPersonImage = personImage.value
  const formJewelryType = jewelryType.value
  const formPersonPosition = personPosition.value
  const formUseVlModel = useVlModel.value

  try {
    // 构建表单数据
    const formData = new FormData()
    formData.append('accessory_image', formJewelryImage)
    formData.append('person_image', formPersonImage)
    formData.append('use_vl_model', formUseVlModel)
    if (formJewelryType) {
      formData.append('accessory_type', formJewelryType)
    }
    if (formPersonPosition) {
      formData.append('person_position', formPersonPosition)
    }

    // 更新任务状态
    updateTask(taskId, { status: 'processing', messageKey: 'tryon.uploading' })

    // 提交任务
    const submitRes = await submitTryOnTask(formData)
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
  const maxAttempts = 120
  let attempts = 0

  // 中文消息到翻译key的映射表（用于处理后端返回的中文消息）
  const messageKeyMap = {
    '准备中...': 'tryon.preparing',
    '正在上传图片...': 'tryon.uploading',
    'VL模型分析饰品中...': 'tryon.vlAnalyzing',
    '试戴图像生成中...': 'tryon.generating',
    '处理中...': 'tryon.processing'
  }

  while (attempts < maxAttempts) {
    try {
      const status = await getTaskStatus(serverTaskId)

      // 将后端返回的中文消息映射到翻译key
      const messageKey = messageKeyMap[status.message] || null
      if (messageKey) {
        updateTask(localTaskId, { messageKey: messageKey })
      } else {
        // 如果没有找到映射，使用原始消息
        updateTask(localTaskId, { message: status.message || t('tryon.processing'), messageKey: null })
      }

      if (status.status === 'completed') {
        const taskResult = await getTaskResult(serverTaskId)
        // 获取任务名称用于提示（动态翻译）
        const task = taskList.value.find(t => t.id === localTaskId)
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

    await new Promise(resolve => setTimeout(resolve, 2500))
    attempts++
  }

  updateTask(localTaskId, { status: 'failed', messageKey: 'tryon.timeout' })
}

// 新建任务
function handleNewTask() {
  // 创建新任务，编号基于当前任务列表数量 + 1
  const taskNumber = taskList.value.length + 1
  const taskId = `local-${Date.now()}`  // 使用时间戳作为唯一ID

  const newTask = {
    id: taskId,
    taskNumber: taskNumber,  // 保存任务编号，在显示时动态翻译
    status: 'waiting_upload',  // 新状态：等待上传
    messageKey: 'tryon.waitingUpload',  // 保存翻译key
    result: null,
    serverTaskId: null,
    originalImages: null  // 暂无原始图片
  }

  taskList.value.unshift(newTask)
  activeTaskId.value = taskId

  // 清空表单，让用户重新上传
  jewelryImage.value = null
  personImage.value = null
}

// 重新生成（在当前任务上重试，而非创建新任务）
async function handleRetry() {
  const currentTask = activeTask.value

  // 检查任务是否存在且有 serverTaskId（后端任务ID）
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

  // 更新当前任务状态为处理中（在当前任务上重试，不创建新任务）
  updateTask(taskId, {
    status: 'processing',
    messageKey: 'tryon.retrying',
    result: null
  })

  try {
    // 构建表单数据
    const formData = new FormData()
    formData.append('use_vl_model', currentTask.originalImages?.useVlModel ?? true)

    // 如果有本地缓存的原始图片，使用它们；否则后端会使用已保存的图片
    if (currentTask.originalImages?.jewelryImage) {
      formData.append('accessory_image', currentTask.originalImages.jewelryImage)
    }
    if (currentTask.originalImages?.personImage) {
      formData.append('person_image', currentTask.originalImages.personImage)
    }
    if (currentTask.originalImages?.jewelryType) {
      formData.append('accessory_type', currentTask.originalImages.jewelryType)
    }
    if (currentTask.originalImages?.personPosition) {
      formData.append('person_position', currentTask.originalImages.personPosition)
    }

    // 调用重新提交API（使用原有的 serverTaskId）
    await resubmitTask(serverTaskId, formData)

    // 开始轮询（使用原有的 serverTaskId）
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

  // 恢复选中任务的图片状态
  const task = taskList.value.find(t => t.id === taskId)
  if (task && task.originalImages) {
    // 如果任务有原始图片，恢复它们
    jewelryImage.value = task.originalImages.jewelryImage
    personImage.value = task.originalImages.personImage
  } else {
    // 如果任务没有图片（如新建的等待上传任务），清空表单
    jewelryImage.value = null
    personImage.value = null
  }
}

// 删除任务
async function handleRemoveTask(taskId) {
  const task = taskList.value.find(t => t.id === taskId)

  // 如果有服务器端任务ID，调用后端API删除
  if (task && task.serverTaskId) {
    try {
      await deleteTask(task.serverTaskId)
    } catch (error) {
      // 即使后端删除失败，也继续删除前端记录（可能任务已过期被清理）
      console.warn('后端删除任务失败:', error)
    }
  }

  // 从前端列表中移除
  const index = taskList.value.findIndex(t => t.id === taskId)
  if (index > -1) {
    if (taskList.value[index].originalImages) {
      revokeObjectUrls(taskList.value[index].originalImages)
    }
    taskList.value.splice(index, 1)
  }

  // 如果删除的是当前活动任务，切换到第一个任务
  if (activeTaskId.value === taskId) {
    activeTaskId.value = taskList.value[0]?.id || ''
  }
}

function revokeObjectUrls(originalImages) {
  try {
    if (originalImages.jewelryImageUrl) {
      URL.revokeObjectURL(originalImages.jewelryImageUrl)
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
        await getTaskStatus(task.serverTaskId)
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
      taskList.value = validatedTasks

      // 恢复处理中的任务，继续轮询状态
      tasksNeedingPoll.forEach(task => {
        console.log(`恢复任务轮询: ${task.taskNumber} (${task.serverTaskId})`)
        pollTaskStatus(task.id, task.serverTaskId)
      })
    }
  } catch (error) {
    console.error('恢复任务列表失败:', error)
  }

  // 恢复活动任务ID
  try {
    const savedActiveTaskId = localStorage.getItem(ACTIVE_TASK_ID_KEY)
    if (savedActiveTaskId) {
      activeTaskId.value = savedActiveTaskId

      // 恢复对应任务的图片状态
      const task = taskList.value.find(t => t.id === savedActiveTaskId)
      if (task && task.originalImages) {
        jewelryImage.value = task.originalImages.jewelryImage
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

.feature-selector {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.feature-selector :deep(.el-radio-button__inner) {
  padding: 12px 24px;
  font-size: 15px;
}

.feature-selector :deep(.el-radio-button.is-disabled .el-radio-button__inner) {
  color: #c0c4cc;
  cursor: not-allowed;
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
