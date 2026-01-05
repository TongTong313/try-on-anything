<template>
  <el-dropdown @command="handleThemeChange" trigger="click">
    <el-button type="primary" circle class="theme-btn">
      <!-- 根据当前主题显示不同图标 -->
      <!-- 深色模式显示月亮图标 -->
      <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
      </svg>
      <!-- 浅色模式显示太阳图标 -->
      <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="5"></circle>
        <line x1="12" y1="1" x2="12" y2="3"></line>
        <line x1="12" y1="21" x2="12" y2="23"></line>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
        <line x1="1" y1="12" x2="3" y2="12"></line>
        <line x1="21" y1="12" x2="23" y2="12"></line>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
      </svg>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="light" :disabled="currentTheme === 'light'">
          <span :class="{ 'active-theme': currentTheme === 'light' }">☀️ {{ $t('theme.light') }}</span>
        </el-dropdown-item>
        <el-dropdown-item command="dark" :disabled="currentTheme === 'dark'">
          <span :class="{ 'active-theme': currentTheme === 'dark' }">🌙 {{ $t('theme.dark') }}</span>
        </el-dropdown-item>
        <el-dropdown-item command="auto" :disabled="currentTheme === 'auto'">
          <span :class="{ 'active-theme': currentTheme === 'auto' }">💻 {{ $t('theme.auto') }}</span>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  applyTheme,
  saveTheme,
  getSavedTheme,
  getSystemTheme,
  watchSystemTheme,
  THEME_LIGHT,
  THEME_DARK,
  THEME_AUTO
} from '../utils/theme'

// 当前主题偏好（light/dark/auto）
const currentTheme = ref(THEME_AUTO)

// 当前实际应用的主题（light/dark）
const actualTheme = ref(THEME_LIGHT)

// 是否为深色模式
const isDark = computed(() => actualTheme.value === THEME_DARK)

// 系统主题监听器的取消函数
let unwatchSystemTheme = null

// 初始化主题
onMounted(() => {
  // 获取保存的主题偏好
  const savedTheme = getSavedTheme()
  if (savedTheme) {
    currentTheme.value = savedTheme
  } else {
    currentTheme.value = THEME_AUTO
  }

  // 应用主题
  updateActualTheme()

  // 如果是自动模式，监听系统主题变化
  if (currentTheme.value === THEME_AUTO) {
    startWatchingSystemTheme()
  }
})

// 组件卸载时取消监听
onUnmounted(() => {
  if (unwatchSystemTheme) {
    unwatchSystemTheme()
  }
})

// 更新实际应用的主题
function updateActualTheme() {
  if (currentTheme.value === THEME_AUTO) {
    actualTheme.value = getSystemTheme()
    applyTheme(actualTheme.value)
  } else {
    actualTheme.value = currentTheme.value
    applyTheme(currentTheme.value)
  }
}

// 开始监听系统主题变化
function startWatchingSystemTheme() {
  unwatchSystemTheme = watchSystemTheme((systemTheme) => {
    // 只有在自动模式下才响应系统主题变化
    if (currentTheme.value === THEME_AUTO) {
      actualTheme.value = systemTheme
      applyTheme(systemTheme)
    }
  })
}

// 停止监听系统主题变化
function stopWatchingSystemTheme() {
  if (unwatchSystemTheme) {
    unwatchSystemTheme()
    unwatchSystemTheme = null
  }
}

// 切换主题
function handleThemeChange(theme) {
  // 更新主题偏好
  currentTheme.value = theme

  // 保存到 localStorage
  saveTheme(theme)

  // 更新实际应用的主题
  updateActualTheme()

  // 管理系统主题监听
  if (theme === THEME_AUTO) {
    startWatchingSystemTheme()
  } else {
    stopWatchingSystemTheme()
  }
}
</script>

<style scoped>
.theme-btn {
  display: flex;
  align-items: center;
  justify-content: center;
}

.active-theme {
  font-weight: bold;
  color: #409eff;
}
</style>
