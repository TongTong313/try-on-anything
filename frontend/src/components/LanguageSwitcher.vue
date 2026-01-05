<template>
  <el-dropdown @command="handleLanguageChange" trigger="click">
    <el-button type="primary" circle class="lang-btn">
      <!-- 地球图标 SVG -->
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="2" y1="12" x2="22" y2="12"></line>
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
      </svg>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="zh-CN" :disabled="currentLocale === 'zh-CN'">
          <span :class="{ 'active-lang': currentLocale === 'zh-CN' }">🇨🇳 中文</span>
        </el-dropdown-item>
        <el-dropdown-item command="en-US" :disabled="currentLocale === 'en-US'">
          <span :class="{ 'active-lang': currentLocale === 'en-US' }">🇺🇸 English</span>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()

// 当前语言
const currentLocale = computed(() => locale.value)

// 切换语言
const handleLanguageChange = (lang) => {
  locale.value = lang
  // 保存到localStorage
  localStorage.setItem('locale', lang)
}
</script>

<style scoped>
.active-lang {
  font-weight: bold;
  color: #409eff;
}
</style>
