<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <el-icon class="logo-icon" :size="48"><Reading /></el-icon>
        <h1 class="title">小说大数据平台</h1>
        <p class="subtitle">Novel Big Data Platform</p>
      </div>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <div class="login-options">
          <el-checkbox v-model="form.remember">记住我</el-checkbox>
        </div>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form-item>
        <div class="login-footer">
          <span>还没有账号？</span>
          <router-link to="/register">立即注册</router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { User, Lock, Reading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '@/api/index'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  remember: false
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 30, message: '密码长度在 6 到 30 个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const res = await request.post('/auth/login', {
          username: form.username,
          password: form.password
        })
        const data = res.data
        userStore.login({
          token: data.token,
          user: {
            userId: data.userId,
            username: data.username,
            avatar: data.avatar || ''
          }
        })
        ElMessage.success('登录成功')
        const redirect = route.query.redirect || '/home'
        router.push(redirect)
      } catch (e) {
        // 拦截器已处理错误提示
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.08) 0%, transparent 60%);
    animation: bgFloat 15s ease-in-out infinite;
  }
}

@keyframes bgFloat {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(30px, -30px); }
}

.login-card {
  width: 420px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: $border-radius-lg;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  padding: 40px 36px;
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 36px;

  .logo-icon {
    color: #667eea;
    margin-bottom: 12px;
  }

  .title {
    font-size: 26px;
    font-weight: 700;
    color: $text-primary;
    margin-bottom: 6px;
    letter-spacing: 2px;
  }

  .subtitle {
    font-size: 13px;
    color: $text-secondary;
    letter-spacing: 1px;
  }
}

.login-form {
  .el-form-item {
    margin-bottom: 22px;
  }

  .el-input {
    --el-input-border-radius: 8px;
  }
}

.login-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.login-btn {
  width: 100%;
  border-radius: 8px;
  font-size: 16px;
  letter-spacing: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  height: 44px;

  &:hover {
    opacity: 0.9;
  }
}

.login-footer {
  text-align: center;
  font-size: 14px;
  color: $text-secondary;

  a {
    color: #667eea;
    font-weight: 500;
    margin-left: 4px;

    &:hover {
      text-decoration: underline;
    }
  }
}
</style>
