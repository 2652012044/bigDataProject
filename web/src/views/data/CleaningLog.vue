<template>
  <div class="cleaning-log-page">
    <div class="page-header">
      <h2 class="page-title">数据清洗日志</h2>
      <p class="page-desc">展示数据导入/清洗过程的执行记录与数据库状态</p>
    </div>

    <!-- 数据库当前状态 -->
    <div class="card-box">
      <div class="card-header">
        <span class="card-title">数据库当前状态</span>
        <el-button size="small" @click="loadDbStats" :loading="loadingStats">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
      <el-row :gutter="16">
        <el-col :span="3" v-for="item in dbStats" :key="item.table">
          <div class="stat-card">
            <div class="stat-value">{{ Number(item.count).toLocaleString() }}</div>
            <div class="stat-label">{{ tableNameMap[item.table] || item.table }}</div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 导入日志时间线 -->
    <div class="card-box">
      <div class="card-header">
        <span class="card-title">导入执行记录</span>
        <el-tag v-if="logs.length > 0" size="small" type="info">共 {{ logs.length }} 次执行</el-tag>
        <el-tag v-else size="small" type="warning">暂无日志记录，请先运行 import_data.py</el-tag>
      </div>

      <div v-if="logs.length === 0" class="empty-state">
        <el-empty description="暂无清洗日志">
          <template #description>
            <p>日志将在运行 <code>python import_data.py</code> 后自动生成</p>
          </template>
        </el-empty>
      </div>

      <el-timeline v-else>
        <el-timeline-item
          v-for="(log, index) in logs"
          :key="index"
          :timestamp="log.start_time"
          placement="top"
          :type="getStatusType(log.status)"
          :hollow="index > 0"
          size="large"
        >
          <el-card shadow="hover" class="log-card">
            <div class="log-header">
              <div class="log-title">
                <el-tag :type="getStatusType(log.status)" effect="dark" size="small">
                  {{ getStatusText(log.status) }}
                </el-tag>
                <span class="log-time">{{ log.start_time }} ~ {{ log.end_time }}</span>
              </div>
              <el-button size="small" text @click="toggleDetail(index)">
                {{ expandedLogs.includes(index) ? '收起' : '展开详情' }}
              </el-button>
            </div>

            <!-- 摘要统计 -->
            <div class="log-summary" v-if="log.summary && Object.keys(log.summary).length > 0">
              <el-tag v-for="(count, table) in log.summary" :key="table" size="small" effect="plain" class="summary-tag">
                {{ tableNameMap[table] || table }}: {{ count }}
              </el-tag>
            </div>

            <!-- 错误信息 -->
            <div v-if="log.errors && log.errors.length > 0" class="log-errors">
              <el-alert v-for="(err, i) in log.errors" :key="i" :title="err" type="error" :closable="false" show-icon />
            </div>

            <!-- 展开的详情 -->
            <div v-if="expandedLogs.includes(index)" class="log-detail">
              <h4>执行步骤</h4>
              <el-table :data="log.steps || []" stripe size="small" style="width: 100%">
                <el-table-column prop="step" label="步骤" width="160" />
                <el-table-column prop="status" label="状态" width="100" align="center">
                  <template #default="{ row }">
                    <el-tag :type="row.status === '成功' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="duration_ms" label="耗时" width="120" align="center">
                  <template #default="{ row }">
                    {{ row.duration_ms != null ? row.duration_ms + 'ms' : '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="detail" label="详情">
                  <template #default="{ row }">
                    {{ row.detail || row.error || '-' }}
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/api/index'

const logs = ref([])
const dbStats = ref([])
const loadingStats = ref(false)
const expandedLogs = ref([])

const tableNameMap = {
  category: '分类', author: '作者', book: '书籍', tag: '标签',
  book_tag: '书籍标签', comment: '评论', web_user: '用户', user_favorite: '收藏'
}

function getStatusType(status) {
  if (status === 'success') return 'success'
  if (status === 'partial') return 'warning'
  if (status === 'failed') return 'danger'
  return 'info'
}

function getStatusText(status) {
  if (status === 'success') return '成功'
  if (status === 'partial') return '部分成功'
  if (status === 'failed') return '失败'
  if (status === 'running') return '运行中'
  return status
}

function toggleDetail(index) {
  const i = expandedLogs.value.indexOf(index)
  if (i >= 0) expandedLogs.value.splice(i, 1)
  else expandedLogs.value.push(index)
}

async function loadLogs() {
  try {
    const res = await request.get('/data/cleaning-logs')
    logs.value = res.data || []
    // 默认展开最新一条
    if (logs.value.length > 0) expandedLogs.value = [0]
  } catch (e) { /* keep empty */ }
}

async function loadDbStats() {
  loadingStats.value = true
  try {
    const res = await request.get('/data/db-stats')
    dbStats.value = res.data || []
  } catch (e) { /* keep empty */ }
  loadingStats.value = false
}

onMounted(() => {
  loadLogs()
  loadDbStats()
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.cleaning-log-page { padding: $spacing-lg; background: $bg-page; min-height: calc(100vh - $top-nav-height); }
.page-header { margin-bottom: $spacing-lg; .page-title { font-size: 22px; font-weight: 700; color: $text-primary; margin: 0 0 6px 0; } .page-desc { font-size: 13px; color: $text-secondary; margin: 0; } }
.card-box { background: $bg-white; border-radius: $border-radius-md; box-shadow: $box-shadow-light; padding: $spacing-lg; margin-bottom: $spacing-lg; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: $spacing-md; .card-title { font-size: 16px; font-weight: 600; color: $text-primary; } }

.stat-card {
  text-align: center; padding: $spacing-md; background: $bg-color; border-radius: $border-radius-md;
  .stat-value { font-size: 24px; font-weight: 700; color: $primary-color; }
  .stat-label { font-size: 12px; color: $text-secondary; margin-top: 4px; }
}

.log-card {
  :deep(.el-card__body) { padding: 16px; }
}

.log-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: $spacing-sm; }
.log-title { display: flex; align-items: center; gap: $spacing-sm; .log-time { font-size: 13px; color: $text-secondary; } }

.log-summary { display: flex; flex-wrap: wrap; gap: $spacing-xs; margin-bottom: $spacing-sm; .summary-tag { font-size: 12px; } }
.log-errors { margin-top: $spacing-sm; display: flex; flex-direction: column; gap: $spacing-xs; }
.log-detail { margin-top: $spacing-md; h4 { font-size: 14px; font-weight: 600; color: $text-primary; margin: 0 0 $spacing-sm 0; } }
.empty-state { padding: 40px 0; text-align: center; code { background: #f5f7fa; padding: 2px 6px; border-radius: 4px; font-size: 13px; } }
</style>
