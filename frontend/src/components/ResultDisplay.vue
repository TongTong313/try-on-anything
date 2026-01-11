<template>
  <div class="result-display">
    <div class="result-header">
      <h3>{{ displayTitle }}</h3>
      <div v-if="jewelryType || personPosition" class="detected-info">
        <el-tag v-if="jewelryType" type="info" size="small">
          {{ translatedJewelryType }}
        </el-tag>
        <el-tag v-if="personPosition" type="success" size="small">
          {{ translatedPersonPosition }}
        </el-tag>
      </div>
    </div>

    <!-- 主要展示：结果图像 -->
    <div class="result-main">
      <img :src="resultImageUrl" class="result-image" />
    </div>

    <!-- 参考信息：原始图片 -->
    <div v-if="originalItemUrl || originalPersonUrl" class="reference-images">
      <div class="reference-label">{{ $t('resultDisplay.originalImage') }}</div>
      <div class="reference-gallery">
        <!-- 原始饰品/服装图 -->
        <div v-if="originalItemUrl" class="reference-item">
          <div class="reference-item-label">{{ itemImageLabel }}</div>
          <img :src="originalItemUrl" class="reference-thumbnail" />
        </div>

        <!-- 原始人物图 -->
        <div v-if="originalPersonUrl" class="reference-item">
          <div class="reference-item-label">{{ $t('resultDisplay.personImage') }}</div>
          <img :src="originalPersonUrl" class="reference-thumbnail" />
        </div>
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
  taskType: { type: String, default: 'accessory' }, // 任务类型：accessory 或 clothing
  jewelryType: { type: String, default: '' },
  personPosition: { type: String, default: '' },
  originalJewelryUrl: { type: String, default: '' }, // 饰品图片URL
  originalClothingUrl: { type: String, default: '' }, // 服装图片URL
  originalPersonUrl: { type: String, default: '' }
})

defineEmits(['retry'])

// 动态标题：根据任务类型显示不同的标题
const displayTitle = computed(() => {
  return props.taskType === 'clothing'
    ? t('resultDisplay.clothingTitle')
    : t('resultDisplay.title')
})

// 动态物品图片URL：根据任务类型选择对应的图片
const originalItemUrl = computed(() => {
  return props.taskType === 'clothing'
    ? props.originalClothingUrl
    : props.originalJewelryUrl
})

// 动态物品图片标签：根据任务类型显示不同的标签
const itemImageLabel = computed(() => {
  return props.taskType === 'clothing'
    ? t('resultDisplay.clothingImage')
    : t('resultDisplay.accessoryImage')
})

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
  '手指': 'tryon.positions.finger',
  '上半身': 'tryon.clothingPositions.upperBody',
  '下半身': 'tryon.clothingPositions.lowerBody',
  '全身': 'tryon.clothingPositions.fullBody'
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

/* 主要展示区域：结果图像 */
.result-main {
  text-align: center;
  margin-bottom: 32px;
}

.result-image {
  max-width: 100%;
  max-height: 600px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(64, 158, 255, 0.3);
  object-fit: contain;
  border: 3px solid #409eff;
}

/* 参考信息区域：原始图片 */
.reference-images {
  margin-bottom: 24px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 12px;
}

.reference-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 12px;
  font-weight: 500;
}

.reference-gallery {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.reference-item {
  text-align: center;
}

.reference-item-label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
}

.reference-thumbnail {
  max-width: 150px;
  max-height: 150px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  object-fit: contain;
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

html.dark .result-image {
  border-color: #60a5fa;
  box-shadow: 0 4px 20px rgba(96, 165, 250, 0.3);
}

html.dark .reference-images {
  background: #1e293b;
}

html.dark .reference-label {
  color: #d1d5db;
}

html.dark .reference-item-label {
  color: #9ca3af;
}
</style>
