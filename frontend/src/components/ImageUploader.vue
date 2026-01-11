<template>
  <div class="image-uploader">
    <el-upload
      class="upload-area"
      drag
      :auto-upload="false"
      :show-file-list="false"
      :on-change="handleFileChange"
      accept="image/*"
    >
      <div v-if="previewUrl" class="preview-container">
        <img :src="previewUrl" class="preview-image" />
        <div class="preview-overlay">
          <el-icon><Refresh /></el-icon>
          <span>{{ $t('imageUploader.clickToChange') }}</span>
        </div>
      </div>
      <div v-else class="upload-placeholder">
        <el-icon class="upload-icon"><Plus /></el-icon>
        <div class="upload-text">{{ label }}</div>
        <div class="upload-hint">{{ $t('imageUploader.clickOrDrag') }}</div>
      </div>
    </el-upload>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  label: { type: String, default: '上传图片' },
  modelValue: { type: File, default: null }
})

const emit = defineEmits(['update:modelValue'])

const previewUrl = ref('')

// 处理文件选择
function handleFileChange(uploadFile) {
  const file = uploadFile.raw
  emit('update:modelValue', file)

  // 生成预览URL
  if (file) {
    previewUrl.value = URL.createObjectURL(file)
  }
}

// 监听外部变化，同步更新预览
// 使用 immediate: true 确保组件挂载时立即检查 modelValue 并生成预览
// 解决：路由切换返回后，从 IndexedDB 恢复的图片无法显示的问题
watch(() => props.modelValue, (newVal, oldVal) => {
  // 释放旧的预览URL，避免内存泄漏
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
  }

  if (!newVal) {
    // 清空预览
    previewUrl.value = ''
  } else if (newVal instanceof File) {
    // 生成新的预览URL
    previewUrl.value = URL.createObjectURL(newVal)
  }
}, { immediate: true })
</script>

<style scoped>
.image-uploader {
  width: 100%;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload) {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  border: 2px dashed #dcdfe6;
  transition: all 0.3s;
}

.upload-area :deep(.el-upload-dragger:hover) {
  border-color: #409eff;
}

.upload-placeholder {
  text-align: center;
  color: #909399;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 8px;
}

.upload-text {
  font-size: 16px;
  color: #606266;
  margin-bottom: 4px;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
}

.preview-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  max-width: 100%;
  max-height: 196px;
  object-fit: contain;
}

.preview-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  transition: opacity 0.3s;
  cursor: pointer;
}

.preview-container:hover .preview-overlay {
  opacity: 1;
}

.preview-overlay .el-icon {
  font-size: 32px;
  margin-bottom: 8px;
}
</style>

<!-- 深色模式适配 -->
<style>
html.dark .upload-area :deep(.el-upload-dragger) {
  border-color: #4a5568;
  background-color: #374151;
}

html.dark .upload-area :deep(.el-upload-dragger:hover) {
  border-color: #60a5fa;
}

html.dark .upload-placeholder {
  color: #d1d5db;
}

html.dark .upload-icon {
  color: #9ca3af;
}

html.dark .upload-text {
  color: #f5f5f5;
}

html.dark .upload-hint {
  color: #d1d5db;
}
</style>
