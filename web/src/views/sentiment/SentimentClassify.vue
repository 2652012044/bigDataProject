<template>
  <div class="sentiment-classify">
    <h2 class="page-title">情感分类</h2>

    <!-- 顶部图表 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="10">
        <div class="card-box">
          <h3 class="card-title">整体情感分布</h3>
          <div ref="doughnutRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :span="14">
        <div class="card-box">
          <h3 class="card-title">情感趋势</h3>
          <div ref="lineRef" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 分类情感分布（下拉选择） -->
    <div class="card-box">
      <div class="cat-select-header">
        <h3 class="card-title">分类情感分布</h3>
        <el-select v-model="selectedCategory" placeholder="选择分类" size="default"
          class="cat-selector" @change="onCategoryChange">
          <el-option v-for="cat in categoryData" :key="cat.category"
            :label="cat.category + ' (' + cat.commentCount + '条评论)'"
            :value="cat.category" />
        </el-select>
      </div>
      <div v-if="selectedCatData" class="cat-detail-panel">
        <el-row :gutter="20">
          <el-col :span="10">
            <div ref="catPieRef" class="cat-pie-chart"></div>
          </el-col>
          <el-col :span="14">
            <div class="cat-info-panel">
              <div class="cat-info-head">
                <div class="cat-info-avatar" :style="{ background: getCatColor(selectedCatData.category) }">
                  {{ selectedCatData.category.charAt(0) }}
                </div>
                <div>
                  <div class="cat-info-name">{{ selectedCatData.category }}</div>
                  <div class="cat-info-meta">{{ selectedCatData.bookCount }} 本书 · {{ selectedCatData.commentCount }} 条评论</div>
                </div>
                <el-tag :type="getOverallType(selectedCatData.overall)" effect="dark" round>
                  {{ selectedCatData.overall }}
                </el-tag>
              </div>
              <div class="cat-stat-cards">
                <div class="mini-stat positive-stat">
                  <span class="mini-num">{{ selectedCatData.positive }}</span>
                  <span class="mini-label">正面 ({{ selectedCatData.positiveRate }}%)</span>
                </div>
                <div class="mini-stat neutral-stat">
                  <span class="mini-num">{{ selectedCatData.neutral }}</span>
                  <span class="mini-label">中性 ({{ selectedCatData.neutralRate }}%)</span>
                </div>
                <div class="mini-stat negative-stat">
                  <span class="mini-num">{{ selectedCatData.negative }}</span>
                  <span class="mini-label">负面 ({{ selectedCatData.negativeRate }}%)</span>
                </div>
              </div>
              <el-button type="primary" plain round @click="openCategoryDialog(selectedCatData)">
                查看该分类全部评论
              </el-button>
            </div>
          </el-col>
        </el-row>
      </div>
      <div v-else class="empty-hint">请选择一个分类查看情感分布</div>
    </div>

    <!-- 分类卡片 -->
    <div class="category-grid">
      <div v-for="cat in categoryData" :key="cat.category" class="category-card"
        @click="openCategoryDialog(cat)">
        <div class="cat-header">
          <div class="cat-avatar" :style="{ background: getCatColor(cat.category) }">
            {{ cat.category.charAt(0) }}
          </div>
          <div class="cat-info">
            <div class="cat-name">{{ cat.category }}</div>
            <div class="cat-meta">{{ cat.bookCount }} 本书 · {{ cat.commentCount }} 条评论</div>
          </div>
          <el-tag :type="getOverallType(cat.overall)" effect="dark" round size="small">
            {{ cat.overall }}
          </el-tag>
        </div>

        <!-- 情感比例条 -->
        <div class="cat-bar">
          <div class="bar-positive" :style="{ width: cat.positiveRate + '%' }"></div>
          <div class="bar-neutral" :style="{ width: cat.neutralRate + '%' }"></div>
          <div class="bar-negative" :style="{ width: cat.negativeRate + '%' }"></div>
        </div>
        <div class="cat-stats">
          <span class="stat-pos">正面 {{ cat.positiveRate }}%</span>
          <span class="stat-neu">中性 {{ cat.neutralRate }}%</span>
          <span class="stat-neg">负面 {{ cat.negativeRate }}%</span>
        </div>

        <div class="cat-detail-hint">点击查看详细评论 →</div>
      </div>
    </div>

    <!-- 评论详情弹窗 -->
    <el-dialog v-model="dialogVisible" :title="currentCategory.category + ' - 评论情感分析'"
      width="900px" destroy-on-close>
      <div v-loading="dialogLoading">
        <!-- 统计栏 -->
        <div class="dialog-summary">
          <div class="summary-head">
            <span class="summary-cat">{{ currentCategory.category }}</span>
            <span class="summary-meta">共 {{ currentCategory.bookCount || 0 }} 本书 · {{ currentCategory.totalComments || 0 }} 条评论</span>
          </div>
          <div class="sentiment-stats">
            <div class="stat-item stat-positive">
              <span class="stat-num">{{ currentCategory.positive || 0 }}</span>
              <span class="stat-label">正面 ({{ currentCategory.positiveRate || 0 }}%)</span>
            </div>
            <div class="stat-item stat-neutral">
              <span class="stat-num">{{ currentCategory.neutral || 0 }}</span>
              <span class="stat-label">中性 ({{ currentCategory.neutralRate || 0 }}%)</span>
            </div>
            <div class="stat-item stat-negative">
              <span class="stat-num">{{ currentCategory.negative || 0 }}</span>
              <span class="stat-label">负面 ({{ currentCategory.negativeRate || 0 }}%)</span>
            </div>
          </div>
        </div>

        <!-- 筛选 -->
        <div class="filter-bar">
          <el-radio-group v-model="commentFilter" size="small">
            <el-radio-button value="all">全部</el-radio-button>
            <el-radio-button value="positive">正面</el-radio-button>
            <el-radio-button value="neutral">中性</el-radio-button>
            <el-radio-button value="negative">负面</el-radio-button>
          </el-radio-group>
          <span class="filter-count">{{ filteredComments.length }} 条</span>
        </div>

        <!-- 评论列表 -->
        <div v-if="filteredComments.length === 0" class="empty-hint">暂无评论</div>
        <div class="comment-list">
          <div v-for="c in filteredComments" :key="c.commentId" class="comment-item">
            <div class="comment-avatar" :class="'av-' + c.sentimentLabel">
              {{ (c.userName || '匿').charAt(0) }}
            </div>
            <div class="comment-body">
              <div class="comment-head">
                <span class="comment-user">{{ c.userName || '匿名用户' }}</span>
                <el-tag size="small" type="info" effect="plain">{{ c.bookName }}</el-tag>
                <span class="comment-time">{{ c.time }}</span>
                <span class="comment-digg" v-if="c.diggCount">{{ c.diggCount }} 赞</span>
              </div>
              <p class="comment-text">{{ c.content }}</p>
            </div>
            <div class="comment-sentiment">
              <el-tag :type="getSentimentType(c.sentimentLabel)" effect="dark" round>
                {{ c.sentimentText }}
              </el-tag>
              <div class="conf-bar">
                <div class="conf-fill" :style="{ width: Math.round((c.sentimentScore || 0) * 100) + '%', background: getSentimentColor(c.sentimentLabel) }"></div>
              </div>
              <span class="conf-text">{{ Math.round((c.sentimentScore || 0) * 100) }}%</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import request from '@/api/index'

const doughnutRef = ref(null)
const lineRef = ref(null)
const catPieRef = ref(null)
let doughnutChart = null
let lineChart = null
let catPieChart = null

const categoryData = ref([])
const selectedCategory = ref('')
const selectedCatData = ref(null)

// 弹窗
const dialogVisible = ref(false)
const dialogLoading = ref(false)
const currentCategory = ref({})
const categoryComments = ref([])
const commentFilter = ref('all')

const filteredComments = computed(() => {
  if (commentFilter.value === 'all') return categoryComments.value
  return categoryComments.value.filter(c => c.sentimentLabel === commentFilter.value)
})

const catColors = [
  'linear-gradient(135deg, #667eea, #764ba2)',
  'linear-gradient(135deg, #f093fb, #f5576c)',
  'linear-gradient(135deg, #4facfe, #00f2fe)',
  'linear-gradient(135deg, #43e97b, #38f9d7)',
  'linear-gradient(135deg, #fa709a, #fee140)',
  'linear-gradient(135deg, #a18cd1, #fbc2eb)',
  'linear-gradient(135deg, #fccb90, #d57eeb)',
  'linear-gradient(135deg, #e0c3fc, #8ec5fc)',
  'linear-gradient(135deg, #ff9a9e, #fad0c4)',
  'linear-gradient(135deg, #a1c4fd, #c2e9fb)'
]

function getCatColor(name) {
  const idx = name.charCodeAt(0) % catColors.length
  return catColors[idx]
}

function getOverallType(v) {
  if (v === '好评') return 'success'
  if (v === '中等') return 'warning'
  return 'danger'
}

function getSentimentType(label) {
  if (label === 'positive') return 'success'
  if (label === 'negative') return 'danger'
  return 'info'
}

function getSentimentColor(label) {
  if (label === 'positive') return '#67c23a'
  if (label === 'negative') return '#f56c6c'
  return '#909399'
}

async function openCategoryDialog(cat) {
  dialogVisible.value = true
  dialogLoading.value = true
  commentFilter.value = 'all'
  currentCategory.value = { category: cat.category }

  try {
    const res = await request.get(`/sentiment/category/${encodeURIComponent(cat.category)}/comments`)
    currentCategory.value = res.data || {}
    categoryComments.value = (res.data || {}).comments || []
  } catch (e) {
    categoryComments.value = []
  } finally {
    dialogLoading.value = false
  }
}

// ========== 数据加载 ==========

async function loadDistribution() {
  try {
    const res = await request.get('/sentiment/distribution')
    initDoughnutChart(res.data)
  } catch (e) {
    initDoughnutChart({ positive: 0, neutral: 0, negative: 0 })
  }
}

async function loadCategoryDistribution() {
  try {
    const res = await request.get('/sentiment/category-distribution')
    categoryData.value = res.data || []
    // 默认选中第一个分类
    if (categoryData.value.length > 0 && !selectedCategory.value) {
      selectedCategory.value = categoryData.value[0].category
      onCategoryChange()
    }
  } catch (e) { /* keep empty */ }
}

function onCategoryChange() {
  selectedCatData.value = categoryData.value.find(c => c.category === selectedCategory.value) || null
  nextTick(() => initCatPieChart())
}

function initCatPieChart() {
  if (!catPieRef.value || !selectedCatData.value) return
  if (catPieChart) catPieChart.dispose()
  catPieChart = echarts.init(catPieRef.value)

  const d = selectedCatData.value
  catPieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 条 ({d}%)' },
    color: ['#67c23a', '#909399', '#f56c6c'],
    series: [{
      name: d.category, type: 'pie', radius: ['42%', '70%'], center: ['50%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 },
      label: { show: true, fontSize: 14, formatter: '{b}\n{c}条 ({d}%)' },
      emphasis: {
        label: { show: true, fontSize: 16, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.2)' }
      },
      data: [
        { value: d.positive || 0, name: '正面' },
        { value: d.neutral || 0, name: '中性' },
        { value: d.negative || 0, name: '负面' }
      ]
    }]
  })
}

async function loadTrend() {
  try {
    const res = await request.get('/sentiment/trend')
    initLineChart(res.data || [])
  } catch (e) {
    initLineChart([])
  }
}

// ========== 图表初始化 ==========

function initDoughnutChart(d) {
  if (!doughnutRef.value) return
  doughnutChart = echarts.init(doughnutRef.value)
  doughnutChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 条 ({d}%)' },
    legend: {
      orient: 'vertical', right: '8%', top: 'center',
      itemWidth: 14, itemHeight: 14, textStyle: { fontSize: 14, color: '#606266' }
    },
    color: ['#67c23a', '#909399', '#f56c6c'],
    series: [{
      name: '情感分布', type: 'pie', radius: ['45%', '72%'], center: ['40%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 },
      label: { show: true, fontSize: 13, formatter: '{b}\n{d}%' },
      emphasis: {
        label: { show: true, fontSize: 16, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.2)' }
      },
      data: [
        { value: d.positive || 0, name: '正面' },
        { value: d.neutral || 0, name: '中性' },
        { value: d.negative || 0, name: '负面' }
      ]
    }]
  })
}

function initLineChart(trendData) {
  if (!lineRef.value) return
  lineChart = echarts.init(lineRef.value)
  lineChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: { data: ['正面', '中性', '负面'], top: 4, textStyle: { fontSize: 13 } },
    grid: { left: '3%', right: '4%', bottom: '3%', top: 50, containLabel: true },
    xAxis: {
      type: 'category', boundaryGap: false, data: trendData.map(d => d.month),
      axisLabel: { fontSize: 12, color: '#606266' }
    },
    yAxis: { type: 'value', axisLabel: { fontSize: 12, color: '#606266' } },
    color: ['#67c23a', '#909399', '#f56c6c'],
    series: [
      { name: '正面', type: 'line', smooth: true, data: trendData.map(d => d.positive), areaStyle: { opacity: 0.08 } },
      { name: '中性', type: 'line', smooth: true, data: trendData.map(d => d.neutral), areaStyle: { opacity: 0.08 } },
      { name: '负面', type: 'line', smooth: true, data: trendData.map(d => d.negative), areaStyle: { opacity: 0.08 } }
    ]
  })
}

const handleResize = () => {
  doughnutChart?.resize()
  lineChart?.resize()
  catPieChart?.resize()
}

onMounted(() => {
  loadDistribution()
  loadCategoryDistribution()
  loadTrend()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  doughnutChart?.dispose()
  lineChart?.dispose()
  catPieChart?.dispose()
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.sentiment-classify { padding: $spacing-lg; }
.page-title { font-size: 22px; font-weight: 600; color: $text-primary; margin-bottom: $spacing-lg; }
.card-box { background: $bg-white; border-radius: $border-radius-md; box-shadow: $box-shadow-light; padding: $spacing-lg; margin-bottom: $spacing-lg; }
.card-title { font-size: 16px; font-weight: 600; color: $text-primary; margin-bottom: $spacing-md; padding-left: $spacing-sm; border-left: 3px solid $primary-color; }
.chart-row { margin-bottom: 0; }
.chart-container { width: 100%; height: 360px; }

/* 分类选择区 */
.cat-select-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
  .card-title { margin-bottom: 0; }
  .cat-selector { width: 280px; }
}

.cat-pie-chart { width: 100%; height: 300px; }

.cat-info-panel {
  display: flex; flex-direction: column; justify-content: center; height: 300px; gap: 20px;
}

.cat-info-head {
  display: flex; align-items: center; gap: 12px;
  .cat-info-avatar {
    width: 48px; height: 48px; border-radius: 12px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; font-weight: 800; color: #fff;
  }
  .cat-info-name { font-size: 18px; font-weight: 700; color: $text-primary; }
  .cat-info-meta { font-size: 13px; color: $text-secondary; margin-top: 2px; }
  .el-tag { margin-left: auto; }
}

.cat-stat-cards {
  display: flex; gap: 12px;
  .mini-stat {
    flex: 1; text-align: center; padding: 14px 8px; border-radius: 10px; background: #f8f9fb;
    .mini-num { display: block; font-size: 22px; font-weight: 700; }
    .mini-label { display: block; font-size: 12px; color: $text-secondary; margin-top: 4px; }
    &.positive-stat .mini-num { color: #67c23a; }
    &.neutral-stat .mini-num { color: #909399; }
    &.negative-stat .mini-num { color: #f56c6c; }
  }
}

/* 分类卡片网格 */
.category-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; margin-bottom: $spacing-lg;
}

.category-card {
  background: $bg-white; border-radius: 14px; padding: 20px;
  box-shadow: $box-shadow-light; cursor: pointer; transition: all 0.3s ease;
  &:hover { transform: translateY(-4px); box-shadow: 0 12px 28px rgba(0, 0, 0, 0.1); }
}

.cat-header {
  display: flex; align-items: center; gap: 12px; margin-bottom: 16px;
  .cat-avatar {
    width: 44px; height: 44px; border-radius: 12px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; font-weight: 800; color: #fff;
  }
  .cat-info { flex: 1; min-width: 0; }
  .cat-name { font-size: 16px; font-weight: 600; color: $text-primary; }
  .cat-meta { font-size: 12px; color: $text-secondary; margin-top: 2px; }
}

.cat-bar {
  display: flex; height: 10px; border-radius: 5px; overflow: hidden; margin-bottom: 8px;
  .bar-positive { background: #67c23a; transition: width 0.5s; }
  .bar-neutral { background: #dcdfe6; transition: width 0.5s; }
  .bar-negative { background: #f56c6c; transition: width 0.5s; }
}

.cat-stats {
  display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 8px;
  .stat-pos { color: #67c23a; font-weight: 600; }
  .stat-neu { color: #909399; }
  .stat-neg { color: #f56c6c; font-weight: 600; }
}

.cat-detail-hint {
  text-align: right; font-size: 12px; color: $primary-color; opacity: 0;
  transition: opacity 0.3s;
  .category-card:hover & { opacity: 1; }
}

/* 弹窗样式 */
.dialog-summary {
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  border-radius: 12px; padding: 20px; margin-bottom: 20px;
  .summary-head { margin-bottom: 16px; }
  .summary-cat { font-size: 20px; font-weight: 700; color: $text-primary; margin-right: 12px; }
  .summary-meta { font-size: 13px; color: $text-secondary; }
}

.sentiment-stats {
  display: flex; gap: 16px;
  .stat-item {
    flex: 1; text-align: center; padding: 12px; border-radius: 8px; background: $bg-white;
    .stat-num { display: block; font-size: 24px; font-weight: 700; }
    .stat-label { display: block; font-size: 12px; color: $text-secondary; margin-top: 4px; }
    &.stat-positive .stat-num { color: #67c23a; }
    &.stat-neutral .stat-num { color: #909399; }
    &.stat-negative .stat-num { color: #f56c6c; }
  }
}

.filter-bar {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid $border-light;
  .filter-count { font-size: 13px; color: $text-secondary; }
}
.empty-hint { text-align: center; color: #909399; padding: 40px; }

.comment-list {
  max-height: 460px; overflow-y: auto;
  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-thumb { background: #ddd; border-radius: 2px; }
}

.comment-item {
  display: flex; gap: 12px; padding: 14px; margin-bottom: 6px;
  border-radius: 10px; background: #fafbfc; transition: background 0.2s;
  &:hover { background: #f0f2f5; }
}

.comment-avatar {
  width: 38px; height: 38px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; font-weight: 700; color: #fff;
  &.av-positive { background: linear-gradient(135deg, #67c23a, #85ce61); }
  &.av-neutral { background: linear-gradient(135deg, #909399, #b1b3b8); }
  &.av-negative { background: linear-gradient(135deg, #f56c6c, #f89898); }
}

.comment-body {
  flex: 1; min-width: 0;
  .comment-head {
    display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px;
    .comment-user { font-weight: 600; font-size: 13px; color: $text-primary; }
    .comment-time { font-size: 12px; color: $text-secondary; }
    .comment-digg { font-size: 12px; color: #e6a23c; }
  }
  .comment-text { font-size: 13px; color: $text-regular; line-height: 1.6; margin: 0; word-break: break-all; }
}

.comment-sentiment {
  flex-shrink: 0; width: 80px; display: flex; flex-direction: column; align-items: center; gap: 4px;
  .conf-bar {
    width: 100%; height: 4px; background: #e8e8e8; border-radius: 2px; overflow: hidden;
    .conf-fill { height: 100%; border-radius: 2px; transition: width 0.5s; }
  }
  .conf-text { font-size: 11px; color: $text-secondary; }
}
</style>
