<template>
  <div class="task-sidebar">
    <div class="sidebar-header">
      <h3>{{ $t('taskSidebar.title') }}</h3>
      <el-button type="primary" size="small" @click="$emit('new-task')">
        <el-icon><Plus /></el-icon>
        {{ $t('taskSidebar.newTask') }}
      </el-button>
    </div>

    <div class="task-list">
      <div
        v-for="task in tasks"
        :key="task.id"
        class="task-item"
        :class="{ active: task.id === activeTaskId, completed: task.status === 'completed', failed: task.status === 'failed' }"
        @click="$emit('select-task', task.id)"
      >
        <div class="task-info">
          <!-- 动态翻译任务名称 -->
          <div class="task-name">{{ $t('tryon.task') }} {{ task.taskNumber }}</div>
          <div class="task-status">
            <el-icon v-if="task.status === 'processing'" class="is-loading"><Loading /></el-icon>
            <el-icon v-else-if="task.status === 'completed'" class="success"><CircleCheck /></el-icon>
            <el-icon v-else-if="task.status === 'failed'" class="error"><CircleClose /></el-icon>
            <el-icon v-else><Clock /></el-icon>
            <!-- 动态翻译状态消息 -->
            <span>{{ task.messageKey ? $t(task.messageKey) : task.message }}</span>
          </div>
        </div>
        <el-button
          v-if="task.status === 'completed' || task.status === 'failed' || task.status === 'waiting_upload'"
          type="danger"
          size="small"
          circle
          @click.stop="$emit('remove-task', task.id)"
        >
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>

      <div v-if="tasks.length === 0" class="empty-tip">
        {{ $t('taskSidebar.emptyTip') }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
defineProps({
  tasks: { type: Array, default: () => [] },
  activeTaskId: { type: String, default: '' }
})

defineEmits(['new-task', 'select-task', 'remove-task'])
</script>

<style scoped>
.task-sidebar {
  width: 280px;
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 120px);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.task-list {
  flex: 1;
  overflow-y: auto;
}

.task-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 8px;
  background: #f5f7fa;
}

.task-item:hover {
  background: #ecf5ff;
}

.task-item.active {
  background: #ecf5ff;
  border: 1px solid #409eff;
}

.task-item.completed {
  background: #f0f9eb;
}

.task-item.failed {
  background: #fef0f0;
}

.task-info {
  flex: 1;
  min-width: 0;
}

.task-name {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.task-status .is-loading {
  animation: rotate 1s linear infinite;
  color: #409eff;
}

.task-status .success {
  color: #67c23a;
}

.task-status .error {
  color: #f56c6c;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-tip {
  text-align: center;
  color: #909399;
  padding: 20px;
  font-size: 14px;
}
</style>

<!-- 深色模式适配 -->
<style>
html.dark .task-sidebar {
  background: #2d3748;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

html.dark .sidebar-header {
  border-bottom: 1px solid #4a5568;
}

html.dark .sidebar-header h3 {
  color: #f5f5f5;
}

html.dark .task-item {
  background: #374151;
}

html.dark .task-item:hover {
  background: #4a5568;
}

html.dark .task-item.active {
  background: #4a5568;
  border: 1px solid #60a5fa;
}

html.dark .task-item.completed {
  background: #1e4620;
}

html.dark .task-item.failed {
  background: #4a1e1e;
}

html.dark .task-name {
  color: #f5f5f5;
}

html.dark .task-status {
  color: #d1d5db;
}

html.dark .empty-tip {
  color: #d1d5db;
}
</style>
