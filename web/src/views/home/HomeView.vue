<template>
  <div class="home-page">
    <!-- 指标卡片 -->
    <el-row :gutter="20" class="metric-row">
      <el-col :span="6" v-for="item in metrics" :key="item.label">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-icon" :style="{ background: item.color }">
            <el-icon :size="28"><component :is="item.icon" /></el-icon>
          </div>
          <div class="metric-info">
            <div class="metric-value">{{ item.value }}</div>
            <div class="metric-label">{{ item.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <div class="card-box">
          <div class="card-header"><span class="card-title">类别排行</span></div>
          <div ref="barChartRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="card-box">
          <div class="card-header"><span class="card-title">标签词云</span></div>
          <div ref="wordCloudRef" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 快捷入口 -->
    <div class="card-box">
      <div class="card-header"><span class="card-title">快捷入口</span></div>
      <el-row :gutter="20">
        <el-col :span="6" v-for="entry in quickEntries" :key="entry.title">
          <div class="quick-entry" @click="$router.push(entry.path)">
            <el-icon :size="36" :style="{ color: entry.color }"><component :is="entry.icon" /></el-icon>
            <span>{{ entry.title }}</span>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 底部区域 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <div class="card-box">
          <div class="card-header"><span class="card-title">今日热门 TOP 5</span></div>
          <div class="hot-list">
            <div v-for="(item, i) in hotNovels" :key="i" class="hot-item">
              <span class="hot-rank" :class="'rank-' + (i + 1)">{{ i + 1 }}</span>
              <span class="hot-name">{{ item.bookName }}</span>
              <span class="hot-heat">{{ item.readCount ? Number(item.readCount).toLocaleString() : '0' }}</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="card-box">
          <div class="card-header"><span class="card-title">最近更新</span></div>
          <div class="update-list">
            <div v-for="(item, i) in recentUpdates" :key="i" class="update-item">
              <el-tag size="small">{{ item.category || '其他' }}</el-tag>
              <span class="update-name">{{ item.bookName }}</span>
              <span class="update-time">{{ item.wordNumber ? (item.wordNumber / 10000).toFixed(1) + '万字' : '' }}</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import 'echarts-wordcloud'
import request from '@/api/index'

const barChartRef = ref(null)
const wordCloudRef = ref(null)
let barChart = null
let wordCloud = null

const metrics = ref([
  { label: '总小说数', value: '...', icon: 'Reading', color: 'linear-gradient(135deg, #667eea, #764ba2)' },
  { label: '今日更新', value: '...', icon: 'DocumentAdd', color: 'linear-gradient(135deg, #43e97b, #38f9d7)' },
  { label: '活跃用户', value: '...', icon: 'User', color: 'linear-gradient(135deg, #fa709a, #fee140)' },
  { label: '平均评分', value: '...', icon: 'Star', color: 'linear-gradient(135deg, #a18cd1, #fbc2eb)' }
])

const quickEntries = [
  { title: '书籍分析', icon: 'DataAnalysis', color: '#409eff', path: '/book/keyword' },
  { title: '情感分析', icon: 'ChatDotSquare', color: '#67c23a', path: '/sentiment/classify' },
  { title: '智能推荐', icon: 'MagicStick', color: '#e6a23c', path: '/recommend/hot' },
  { title: '市场趋势', icon: 'TrendCharts', color: '#f56c6c', path: '/trend/type' }
]

const hotNovels = ref([])
const recentUpdates = ref([])

async function loadOverview() {
  try {
    const res = await request.get('/stats/overview')
    const d = res.data
    metrics.value[0].value = Number(d.totalNovel).toLocaleString()
    metrics.value[1].value = String(d.todayUpdates)
    metrics.value[2].value = Number(d.activeUsers).toLocaleString()
    metrics.value[3].value = String(d.averageScore)
  } catch (e) { /* 保持默认值 */ }
}

async function loadCategoryRank() {
  try {
    const res = await request.get('/stats/category-rank')
    const data = (res.data || []).slice(0, 15)
    // 反转使最大值在顶部
    const names = data.map(i => i.categoryName).reverse()
    const values = data.map(i => i.bookCount).reverse()
    initBarChart(names, values)
  } catch (e) {
    initBarChart([], [])
  }
}

async function loadTagCloud() {
  try {
    const res = await request.get('/home/tag-cloud')
    const data = res.data || []
    initWordCloud(data)
  } catch (e) {
    initWordCloud([])
  }
}

async function loadHotBooks() {
  try {
    const res = await request.get('/home/hot-books', { params: { limit: 5 } })
    hotNovels.value = res.data || []
  } catch (e) { /* 空列表 */ }
}

async function loadRecentBooks() {
  try {
    const res = await request.get('/home/recent-books', { params: { limit: 5 } })
    recentUpdates.value = res.data || []
  } catch (e) { /* 空列表 */ }
}

function initBarChart(names, values) {
  if (!barChartRef.value) return
  barChart = echarts.init(barChartRef.value)
  const maxVal = Math.max(...values, 1)
  barChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: params => `${params[0].name}：${params[0].value} 部`
    },
    grid: { left: 100, right: 60, top: 10, bottom: 10 },
    xAxis: { type: 'value', show: false },
    yAxis: {
      type: 'category',
      data: names,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { fontSize: 13, color: '#606266' }
    },
    series: [{
      type: 'bar',
      data: values.map((v, i) => ({
        value: v,
        itemStyle: {
          borderRadius: [0, 4, 4, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: i >= values.length - 3 ? '#667eea' : '#409eff' },
            { offset: 1, color: i >= values.length - 3 ? '#764ba2' : '#79bbff' }
          ])
        }
      })),
      barWidth: 16,
      label: {
        show: true,
        position: 'right',
        fontSize: 12,
        color: '#909399',
        formatter: '{c}'
      }
    }]
  })
}

function initWordCloud(words) {
  if (!wordCloudRef.value) return
  wordCloud = echarts.init(wordCloudRef.value)
  wordCloud.setOption({
    series: [{
      type: 'wordCloud',
      shape: 'circle',
      sizeRange: [14, 56],
      rotationRange: [-45, 45],
      gridSize: 8,
      textStyle: {
        fontFamily: 'sans-serif',
        fontWeight: 'bold',
        color: () => {
          const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#764ba2', '#43e97b']
          return colors[Math.floor(Math.random() * colors.length)]
        }
      },
      data: words
    }]
  })
}

const handleResize = () => {
  barChart?.resize()
  wordCloud?.resize()
}

onMounted(() => {
  loadOverview()
  loadCategoryRank()
  loadTagCloud()
  loadHotBooks()
  loadRecentBooks()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  barChart?.dispose()
  wordCloud?.dispose()
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.home-page {
  padding: $spacing-lg;
  min-height: 100%;
}

.metric-row { margin-bottom: $spacing-lg; }

.metric-card {
  :deep(.el-card__body) {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    padding: 20px;
  }
}

.metric-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.metric-info {
  .metric-value {
    font-size: 24px;
    font-weight: 700;
    color: $text-primary;
  }
  .metric-label {
    font-size: 13px;
    color: $text-secondary;
    margin-top: 2px;
  }
}

.card-box {
  background: $bg-white;
  border-radius: $border-radius-md;
  box-shadow: $box-shadow-light;
  padding: $spacing-lg;
  margin-bottom: $spacing-lg;
}

.card-header {
  margin-bottom: $spacing-md;
  .card-title {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
  }
}

.chart-container {
  width: 100%;
  height: 400px;
}

.quick-entry {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-sm;
  padding: $spacing-lg;
  border-radius: $border-radius-md;
  background: $bg-color;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    transform: translateY(-4px);
    box-shadow: $box-shadow;
  }

  span {
    font-size: 14px;
    font-weight: 500;
    color: $text-primary;
  }
}

.hot-list {
  .hot-item {
    display: flex;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid $border-light;

    &:last-child { border-bottom: none; }
  }

  .hot-rank {
    width: 24px;
    height: 24px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
    color: #fff;
    background: $info-color;
    margin-right: 12px;

    &.rank-1 { background: #f56c6c; }
    &.rank-2 { background: #e6a23c; }
    &.rank-3 { background: #409eff; }
  }

  .hot-name {
    flex: 1;
    font-size: 14px;
    color: $text-primary;
  }

  .hot-heat {
    font-size: 13px;
    color: $text-secondary;
  }
}

.update-list {
  .update-item {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    padding: 10px 0;
    border-bottom: 1px solid $border-light;

    &:last-child { border-bottom: none; }
  }

  .update-name {
    flex: 1;
    font-size: 14px;
    color: $text-primary;
  }

  .update-time {
    font-size: 12px;
    color: $text-secondary;
    flex-shrink: 0;
  }
}
</style>
