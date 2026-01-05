<template>
  <div class="result-display">
    <div class="result-header">
      <h3>{{ $t('resultDisplay.title') }}</h3>
      <div v-if="jewelryType || personPosition" class="detected-info">
        <el-tag v-if="jewelryType" type="info" size="small">
          {{ translatedJewelryType }}
        </el-tag>
        <el-tag v-if="personPosition" type="success" size="small">
          {{ translatedPersonPosition }}
        </el-tag>
      </div>
    </div>

    <!-- 显示原始上传的图片和效果图 -->
    <div class="image-gallery">
      <!-- 原始饰品图 -->
      <div v-if="originalJewelryUrl" class="gallery-item">
        <div class="gallery-label">{{ $t('resultDisplay.accessoryImage') }}</div>
        <img :src="originalJewelryUrl" class="gallery-image" />
      </div>

      <!-- 原始人物图 -->
      <div v-if="originalPersonUrl" class="gallery-item">
        <div class="gallery-label">{{ $t('resultDisplay.personImage') }}</div>
        <img :src="originalPersonUrl" class="gallery-image" />
      </div>

      <!-- 箭头 -->
      <div class="gallery-arrow">
        <el-icon><Right /></el-icon>
      </div>

      <!-- 效果图 -->
      <div class="gallery-item highlight">
        <div class="gallery-label">{{ $t('resultDisplay.resultImage') }}</div>
        <img :src="resultImageUrl" class="gallery-image" />
      </div>
    </div>

    <div class="result-actions">
      <el-button type="primary" @click="downloadImage">
        <el-icon><Download /></el-icon>
        {{ $t('resultDisplay.downloadResult') }}
      </el-button>
      <el-button @click="$emit('retry')">
        <el-icon><Refresh /></el-icon>
        {{ $t('resultDisplay.retry') }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  resultImageUrl: { type: String, required: true },
  jewelryType: { type: String, default: '' },
  personPosition: { type: String, default: '' },
  originalJewelryUrl: { type: String, default: '' },
  originalPersonUrl: { type: String, default: '' }
})

defineEmits(['retry'])

// 饰品类型中文到翻译key的映射
const jewelryTypeMap = {
  '项链': 'tryon.types.necklace',
  '耳环': 'tryon.types.earring',
  '手表': 'tryon.types.watch',
  '手链': 'tryon.types.bracelet',
  '手镯': 'tryon.types.bracelet',
  '戒指': 'tryon.types.ring'
}

// 佩戴位置中文到翻译key的映射
const positionMap = {
  '脖子': 'tryon.positions.neck',
  '颈部': 'tryon.positions.neck',
  '耳朵': 'tryon.positions.ear',
  '耳部': 'tryon.positions.ear',
  '手腕': 'tryon.positions.wrist',
  '手指': 'tryon.positions.finger'
}

// 翻译饰品类型
const translatedJewelryType = computed(() => {
  if (!props.jewelryType) return ''
  const key = jewelryTypeMap[props.jewelryType]
  return key ? t(key) : props.jewelryType
})

// 翻译佩戴位置
const translatedPersonPosition = computed(() => {
  if (!props.personPosition) return ''
  const key = positionMap[props.personPosition]
  return key ? t(key) : props.personPosition
})

// 下载效果图
function downloadImage() {
  // 创建一个临时的a标签来触发下载
  const link = document.createElement('a')
  link.href = props.resultImageUrl
  link.download = `tryon-result-${Date.now()}.jpg`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>

<style scoped>
.result-display {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.result-header h3 {
  margin: 0;
  color: #303133;
}

.detected-info {
  display: flex;
  gap: 8px;
}

.image-gallery {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.gallery-item {
  flex: 0 1 auto;
  text-align: center;
  max-width: 280px;
}

.gallery-item.highlight {
  border: 2px solid #409eff;
  border-radius: 12px;
  padding: 8px;
  background: #f0f9ff;
}

.gallery-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
  font-weight: 500;
}

.gallery-item.highlight .gallery-label {
  color: #409eff;
}

.gallery-image {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  object-fit: contain;
}

.gallery-arrow {
  font-size: 24px;
  color: #409eff;
  flex-shrink: 0;
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
}
</style>

<!-- 深色模式适配 -->
<style>
html.dark .result-display {
  background: #2d3748;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

html.dark .result-header h3 {
  color: #f5f5f5;
}

html.dark .gallery-item.highlight {
  border-color: #60a5fa;
  background: #1e3a5f;
}

html.dark .gallery-label {
  color: #d1d5db;
}

html.dark .gallery-item.highlight .gallery-label {
  color: #60a5fa;
}
</style>
