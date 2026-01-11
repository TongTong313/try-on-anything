<template>
  <div class="task-sidebar">
    <!-- 标题栏：左侧标题 + 右侧图标按钮 -->
    <div class="sidebar-header">
      <h3>{{ $t('taskSidebar.title') }}</h3>
      <div class="header-actions">
        <!-- 新建任务下拉菜单 -->
        <el-dropdown @command="handleNewTask" trigger="click">
          <el-button type="primary" size="small" class="new-task-dropdown">
            <el-icon><Plus /></el-icon>
            <span>{{ $t('taskSidebar.newTask') }}</span>
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="accessory">
                <el-icon><Star /></el-icon>
                {{ $t('taskSidebar.newAccessoryTask') }}
              </el-dropdown-item>
              <el-dropdown-item command="clothing">
                <el-icon><ShoppingBag /></el-icon>
                {{ $t('taskSidebar.newClothingTask') }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
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
          <!-- 任务名称和类型标签 -->
          <div class="task-name">
            {{ $t('tryon.task') }} {{ task.taskNumber }}
            <el-tag size="small" :type="task.taskType === 'accessory' ? 'primary' : 'success'" class="task-type-tag">
              {{ task.taskType === 'accessory' ? $t('taskSidebar.accessory') : $t('taskSidebar.clothing') }}
            </el-tag>
          </div>
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

      <!-- 空状态提示 -->
      <div v-if="tasks.length === 0" class="empty-state">
        <div class="empty-icon">
          <el-icon><FolderOpened /></el-icon>
        </div>
        <div class="empty-text">{{ $t('taskSidebar.emptyTip') }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { Plus, ArrowDown, Star, ShoppingBag, FolderOpened } from '@element-plus/icons-vue'

const { t } = useI18n()

// 定义 props 和 emits
defineProps({
  tasks: { type: Array, default: () => [] },
  activeTaskId: { type: String, default: '' }
})

const emit = defineEmits(['new-task', 'select-task', 'remove-task'])

// 处理下拉菜单选择
const handleNewTask = (taskType) => {
  emit('new-task', taskType)
}
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
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

/* 标题栏右侧按钮组 */
.header-actions {
  display: flex;
  gap: 8px;
}

/* 下拉菜单按钮样式 */
.new-task-dropdown {
  font-size: 13px;
  padding: 0 12px;
  height: 28px;
}

.new-task-dropdown .el-icon--right {
  margin-left: 4px;
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
  display: flex;
  align-items: center;
  gap: 6px;
}

.task-type-tag {
  flex-shrink: 0;
  font-size: 10px;
  padding: 0 4px;
  height: 18px;
  line-height: 16px;
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

/* 空状态样式 - 醒目的引导提示 */
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

.empty-icon {
  font-size: 48px;
  color: #dcdfe6;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 14px;
  color: #909399;
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

html.dark .empty-state {
  color: #d1d5db;
}

html.dark .empty-icon {
  color: #6b7280;
}

html.dark .empty-text {
  color: #d1d5db;
}
</style>
