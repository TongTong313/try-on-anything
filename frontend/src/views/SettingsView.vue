<template>
  <div class="settings-container">
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <h2>{{ $t('settings.title') }}</h2>
        </div>
      </template>

      <!-- 菜单切换 -->
      <el-tabs v-model="activeMenu" class="settings-tabs">
        <!-- 通用设置标签页 -->
        <el-tab-pane :label="$t('settings.menuGeneral')" name="general">
          <el-form :model="generalForm" label-width="150px" label-position="left">
            <el-divider content-position="left">{{ $t('settings.languageConfig') }}</el-divider>

            <el-form-item :label="$t('settings.language')">
              <el-select v-model="generalForm.language" @change="handleLanguageChange">
                <el-option label="中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- API配置标签页 -->
        <el-tab-pane :label="$t('settings.menuApi')" name="api">
          <el-form :model="form" label-width="150px" label-position="left">
        <el-divider content-position="left">{{ $t('settings.apiConfig') }}</el-divider>

        <!-- API配置说明 -->
        <el-alert
          :title="$t('settings.apiConfigNote')"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 20px"
        />

        <el-form-item :label="$t('settings.configMethod')">
          <el-radio-group v-model="form.configMethod">
            <el-radio value="env">{{ $t('settings.useEnvVar') }}</el-radio>
            <el-radio value="manual">{{ $t('settings.manualInput') }}</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 环境变量设置指南 -->
        <el-alert
          v-if="form.configMethod === 'env'"
          :title="$t('settings.envVarGuide')"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
          class="env-alert"
        >
          <div class="env-guide">
            <div class="command-section">
              <div class="command-header">
                <h4>{{ $t('settings.envVarGuideWindows') }}</h4>
                <el-button
                  size="small"
                  @click="copyToClipboard(windowsEnvCommand)"
                  :icon="CopyDocument"
                >
                  复制
                </el-button>
              </div>
              <pre class="command-block"><code>{{ windowsEnvCommand }}</code></pre>
            </div>

            <div class="command-section">
              <div class="command-header">
                <h4>{{ $t('settings.envVarGuideLinux') }}</h4>
                <el-button
                  size="small"
                  @click="copyToClipboard(linuxEnvCommand)"
                  :icon="CopyDocument"
                >
                  复制
                </el-button>
              </div>
              <pre class="command-block"><code>{{ linuxEnvCommand }}</code></pre>
            </div>
          </div>
        </el-alert>

        <!-- VL模型配置 -->
        <el-divider content-position="left">{{ $t('settings.vlModelConfig') }}</el-divider>

        <el-form-item :label="$t('settings.provider')">
          <el-input :value="$t('settings.providerDashScope')" disabled />
        </el-form-item>

        <el-form-item :label="$t('settings.modelName')">
          <el-select v-model="form.vlModel">
            <el-option label="qwen3-vl-plus" value="qwen3-vl-plus" />
            <el-option label="qwen3-vl-flash" value="qwen3-vl-flash" />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('settings.apiKey')" v-if="form.configMethod === 'manual'">
          <el-input
            v-model="form.vlApiKey"
            :type="showVlApiKey ? 'text' : 'password'"
            :placeholder="$t('settings.apiKeyPlaceholder')"
            clearable
          >
            <template #append>
              <el-button @click="showVlApiKey = !showVlApiKey">
                <el-icon><View v-if="!showVlApiKey" /><Hide v-else /></el-icon>
              </el-button>
            </template>
          </el-input>
          <div class="api-key-actions">
            <el-button size="small" @click="handleTestVlConnection" :loading="testingVl">
              {{ $t('settings.testConnection') }}
            </el-button>
            <span class="api-key-note">
              {{ $t('settings.apiKeyNote') }}
              <el-link :href="$t('settings.applyUrl')" target="_blank" type="primary">
                {{ $t('settings.applyApiKey') }}
              </el-link>
            </span>
          </div>
        </el-form-item>

        <!-- 图像生成模型配置 -->
        <el-divider content-position="left">{{ $t('settings.imageModelConfig') }}</el-divider>

        <el-form-item :label="$t('settings.provider')">
          <el-input :value="$t('settings.providerDashScope')" disabled />
        </el-form-item>

        <el-form-item :label="$t('settings.modelName')">
          <el-select v-model="form.imgGenModel">
            <el-option label="wan2.6-image" value="wan2.6-image" />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('settings.apiKey')" v-if="form.configMethod === 'manual'">
          <el-input
            v-model="form.imageApiKey"
            :type="showImageApiKey ? 'text' : 'password'"
            :placeholder="$t('settings.apiKeyPlaceholder')"
            clearable
          >
            <template #append>
              <el-button @click="showImageApiKey = !showImageApiKey">
                <el-icon><View v-if="!showImageApiKey" /><Hide v-else /></el-icon>
              </el-button>
            </template>
          </el-input>
          <div class="api-key-actions">
            <el-button size="small" @click="handleTestImageConnection" :loading="testingImage">
              {{ $t('settings.testConnection') }}
            </el-button>
            <span class="api-key-note">
              {{ $t('settings.apiKeyNote') }}
              <el-link :href="$t('settings.applyUrl')" target="_blank" type="primary">
                {{ $t('settings.applyApiKey') }}
              </el-link>
            </span>
          </div>
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <el-button type="primary" @click="handleSave" :loading="saving">
            {{ $t('settings.saveSettings') }}
          </el-button>
        </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 功能配置标签页 -->
        <el-tab-pane :label="$t('settings.menuFeatures')" name="features">
          <el-form :model="featuresForm" label-width="150px" label-position="left">
            <el-divider content-position="left">{{ $t('settings.featuresConfig') }}</el-divider>

            <!-- VL模型增强（通用） -->
            <el-form-item :label="$t('settings.vlModelEnhance')">
              <el-switch v-model="featuresForm.useVlModel" />
              <el-text class="vl-tip" type="warning" size="small">
                {{ $t('settings.vlModelEnhanceTip') }}
              </el-text>
            </el-form-item>

            <!-- 饰品试戴配置 -->
            <el-divider content-position="left">{{ $t('settings.accessoryTryonConfig') }}</el-divider>

            <!-- 饰品类型 -->
            <el-form-item :label="$t('settings.accessoryType')">
              <el-select v-model="featuresForm.jewelryType" :placeholder="$t('settings.autoDetect')" clearable>
                <el-option :label="$t('tryon.types.necklace')" value="项链" />
                <el-option :label="$t('tryon.types.earring')" value="耳环" />
                <el-option :label="$t('tryon.types.watch')" value="手表" />
                <el-option :label="$t('tryon.types.bracelet')" value="手链" />
                <el-option :label="$t('tryon.types.ring')" value="戒指" />
              </el-select>
            </el-form-item>

            <!-- 佩戴位置 -->
            <el-form-item :label="$t('settings.personPosition')">
              <el-select v-model="featuresForm.personPosition" :placeholder="$t('settings.autoDetect')" clearable>
                <el-option :label="$t('tryon.positions.neck')" value="脖子" />
                <el-option :label="$t('tryon.positions.ear')" value="耳朵" />
                <el-option :label="$t('tryon.positions.wrist')" value="手腕" />
                <el-option :label="$t('tryon.positions.finger')" value="手指" />
              </el-select>
            </el-form-item>

            <!-- 服装试穿配置 -->
            <el-divider content-position="left">{{ $t('settings.clothingTryonConfig') }}</el-divider>

            <!-- 服装类型 -->
            <el-form-item :label="$t('settings.clothingType')">
              <el-select v-model="featuresForm.clothingType" :placeholder="$t('settings.autoDetect')" clearable>
                <el-option :label="$t('tryon.clothingTypes.top')" value="上衣" />
                <el-option :label="$t('tryon.clothingTypes.pants')" value="裤子" />
                <el-option :label="$t('tryon.clothingTypes.skirt')" value="裙子" />
                <el-option :label="$t('tryon.clothingTypes.jacket')" value="外套" />
              </el-select>
            </el-form-item>

            <!-- 穿着位置 -->
            <el-form-item :label="$t('settings.wearingPosition')">
              <el-select v-model="featuresForm.wearingPosition" :placeholder="$t('settings.autoDetect')" clearable>
                <el-option :label="$t('tryon.clothingPositions.upperBody')" value="上半身" />
                <el-option :label="$t('tryon.clothingPositions.lowerBody')" value="下半身" />
                <el-option :label="$t('tryon.clothingPositions.fullBody')" value="全身" />
              </el-select>
            </el-form-item>

            <!-- 操作按钮 -->
            <el-form-item>
              <el-button type="primary" @click="handleSaveFeatures" :loading="saving">
                {{ $t('settings.saveSettings') }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { CopyDocument, View, Hide } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { saveApiKey, getApiKey } from '../utils/crypto'

const { t, locale } = useI18n()
const route = useRoute()

// 当前激活的菜单
const activeMenu = ref('general')

// 通用设置表单数据
const generalForm = reactive({
  language: locale.value
})

// API配置表单数据
const form = reactive({
  configMethod: 'env', // 'env' 或 'manual'
  vlApiKey: '',
  imageApiKey: '',
  vlModel: 'qwen3-vl-plus',
  imgGenModel: 'wan2.6-image'
})

// 功能配置表单数据
const featuresForm = reactive({
  useVlModel: true,
  jewelryType: '',
  personPosition: '',
  clothingType: '',
  wearingPosition: ''
})

// 显示/隐藏API Key
const showVlApiKey = ref(false)
const showImageApiKey = ref(false)

// 加载和保存状态
const saving = ref(false)
const testingVl = ref(false)
const testingImage = ref(false)

// 环境变量命令
const windowsEnvCommand = computed(() => {
  return `# ${t('settings.windowsCommand')}\n$env:DASHSCOPE_API_KEY="your-api-key-here"\n\n# ${t('settings.windowsPermanent')}\n[System.Environment]::SetEnvironmentVariable('DASHSCOPE_API_KEY', 'your-api-key-here', 'User')`
})

const linuxEnvCommand = computed(() => {
  return `# ${t('settings.linuxCommand')}\nexport DASHSCOPE_API_KEY="your-api-key-here"\n\n# ${t('settings.linuxPermanent')}\necho 'export DASHSCOPE_API_KEY="your-api-key-here"' >> ~/.bashrc\nsource ~/.bashrc`
})

// 复制到剪贴板
const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage({
      message: t('common.success'),
      type: 'success',
      duration: 2000,
      showClose: true,
      offset: 60
    })
  } catch (error) {
    ElMessage({
      message: t('common.error'),
      type: 'error',
      duration: 2000,
      showClose: true,
      offset: 60
    })
  }
}

// 切换语言
const handleLanguageChange = (lang) => {
  locale.value = lang
  localStorage.setItem('locale', lang)
  ElMessage({
    message: t('settings.languageChanged'),
    type: 'success',
    duration: 2000,
    showClose: true,
    offset: 60
  })
}

// 保存设置
const handleSave = () => {
  saving.value = true

  try {
    // 保存配置方式
    localStorage.setItem('configMethod', form.configMethod)

    // 保存模型选择
    localStorage.setItem('vlModel', form.vlModel)
    localStorage.setItem('imgGenModel', form.imgGenModel)

    // 如果是手动输入模式，保存API Key（加密存储）
    if (form.configMethod === 'manual') {
      saveApiKey('vlApiKey', form.vlApiKey)
      saveApiKey('imageApiKey', form.imageApiKey)
    }

    ElMessage({
      message: t('settings.saveSuccess'),
      type: 'success',
      duration: 2000,
      showClose: true,
      offset: 60
    })
  } catch (error) {
    console.error('保存设置失败:', error)
    ElMessage({
      message: t('settings.saveFailed'),
      type: 'error',
      duration: 2000,
      showClose: true,
      offset: 60
    })
  } finally {
    saving.value = false
  }
}

// 保存功能设置
const handleSaveFeatures = () => {
  saving.value = true

  try {
    // 保存功能配置到localStorage
    localStorage.setItem('useVlModel', featuresForm.useVlModel.toString())
    localStorage.setItem('defaultJewelryType', featuresForm.jewelryType)
    localStorage.setItem('defaultPersonPosition', featuresForm.personPosition)
    localStorage.setItem('defaultClothingType', featuresForm.clothingType)
    localStorage.setItem('defaultWearingPosition', featuresForm.wearingPosition)

    ElMessage({
      message: t('settings.saveSuccess'),
      type: 'success',
      duration: 2000,
      showClose: true,
      offset: 60
    })
  } catch (error) {
    console.error('保存设置失败:', error)
    ElMessage({
      message: t('settings.saveFailed'),
      type: 'error',
      duration: 2000,
      showClose: true,
      offset: 60
    })
  } finally {
    saving.value = false
  }
}

// 测试VL模型连接
const handleTestVlConnection = async () => {
  if (!form.vlApiKey || !form.vlApiKey.trim()) {
    ElMessage({
      message: t('settings.apiKeyEmpty'),
      type: 'warning',
      duration: 2000,
      showClose: true,
      offset: 60
    })
    return
  }

  testingVl.value = true

  try {
    const response = await fetch('/api/tryon/test-connection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: form.vlApiKey })
    })

    const result = await response.json()

    if (result.success) {
      ElMessage({
        message: t('settings.vlTestSuccess'),
        type: 'success',
        duration: 2000,
        showClose: true,
        offset: 60
      })
    } else {
      ElMessage({
        message: result.message || t('settings.testFailed'),
        type: 'error',
        duration: 3000,
        showClose: true,
        offset: 60
      })
    }
  } catch (error) {
    console.error('VL模型测试连接失败:', error)
    ElMessage({
      message: t('settings.testFailed'),
      type: 'error',
      duration: 2000,
      showClose: true,
      offset: 60
    })
  } finally {
    testingVl.value = false
  }
}

// 测试图像生成模型连接
const handleTestImageConnection = async () => {
  if (!form.imageApiKey || !form.imageApiKey.trim()) {
    ElMessage({
      message: t('settings.apiKeyEmpty'),
      type: 'warning',
      duration: 2000,
      showClose: true,
      offset: 60
    })
    return
  }

  testingImage.value = true

  try {
    const response = await fetch('/api/tryon/test-connection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: form.imageApiKey })
    })

    const result = await response.json()

    if (result.success) {
      ElMessage({
        message: t('settings.imageTestSuccess'),
        type: 'success',
        duration: 2000,
        showClose: true,
        offset: 60
      })
    } else {
      ElMessage({
        message: result.message || t('settings.testFailed'),
        type: 'error',
        duration: 3000,
        showClose: true,
        offset: 60
      })
    }
  } catch (error) {
    console.error('图像生成模型测试连接失败:', error)
    ElMessage({
      message: t('settings.testFailed'),
      type: 'error',
      duration: 2000,
      showClose: true,
      offset: 60
    })
  } finally {
    testingImage.value = false
  }
}

// 加载保存的设置
onMounted(() => {
  // 从URL查询参数读取tab设置
  const tabParam = route.query.tab
  if (tabParam && ['general', 'api', 'features'].includes(tabParam)) {
    activeMenu.value = tabParam
  }

  const savedMethod = localStorage.getItem('configMethod')
  if (savedMethod) {
    form.configMethod = savedMethod
  }

  // 加载模型选择
  const savedVlModel = localStorage.getItem('vlModel')
  if (savedVlModel) {
    form.vlModel = savedVlModel
  }

  const savedImgGenModel = localStorage.getItem('imgGenModel')
  if (savedImgGenModel) {
    form.imgGenModel = savedImgGenModel
  }

  // 如果是手动输入模式，加载保存的API Key
  if (form.configMethod === 'manual') {
    form.vlApiKey = getApiKey('vlApiKey')
    form.imageApiKey = getApiKey('imageApiKey')
  }

  // 加载功能配置
  const savedUseVlModel = localStorage.getItem('useVlModel')
  if (savedUseVlModel !== null) {
    featuresForm.useVlModel = savedUseVlModel === 'true'
  }

  const savedJewelryType = localStorage.getItem('defaultJewelryType')
  if (savedJewelryType) {
    featuresForm.jewelryType = savedJewelryType
  }

  const savedPersonPosition = localStorage.getItem('defaultPersonPosition')
  if (savedPersonPosition) {
    featuresForm.personPosition = savedPersonPosition
  }

  const savedClothingType = localStorage.getItem('defaultClothingType')
  if (savedClothingType) {
    featuresForm.clothingType = savedClothingType
  }

  const savedWearingPosition = localStorage.getItem('defaultWearingPosition')
  if (savedWearingPosition) {
    featuresForm.wearingPosition = savedWearingPosition
  }
})
</script>

<style scoped>
.settings-container {
  max-width: 900px;
  margin: 0 auto;
}

.settings-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.card-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.settings-tabs {
  margin-top: -10px;
}

.vl-tip {
  margin-left: 12px;
}

.env-guide {
  padding: 12px 0;
  width: 100%;
}

.env-alert :deep(.el-alert__content) {
  padding-right: 0 !important;
  flex: 1;
  width: 100%;
}

.command-section {
  margin-bottom: 20px;
  width: 100%;
}

.command-section:last-child {
  margin-bottom: 0;
}

.command-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.command-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #606266;
}

.command-block {
  background-color: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 20px 24px;
  margin: 0;
  width: 100%;
  min-height: 120px;
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.8;
  color: #303133;
  white-space: pre-wrap;
  word-wrap: break-word;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  box-sizing: border-box;
}

.command-block code {
  background: none;
  padding: 0;
  font-family: inherit;
  font-size: inherit;
  color: inherit;
}

.api-key-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
}

.api-key-note {
  font-size: 12px;
  color: #909399;
}

:deep(.el-divider__text) {
  font-size: 16px;
  font-weight: 600;
}
</style>

<!-- 深色模式适配 -->
<style>
html.dark .command-header h4 {
  color: #f5f5f5;
}

html.dark .command-block {
  background-color: #374151;
  border-color: #4a5568;
  color: #f5f5f5;
}

html.dark .api-key-note {
  color: #d1d5db;
}
</style>
