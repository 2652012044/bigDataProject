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
              <span class="hot-name">{{ item.name }}</span>
              <span class="hot-heat">{{ item.heat }}</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="card-box">
          <div class="card-header"><span class="card-title">最近更新</span></div>
          <div class="update-list">
            <div v-for="(item, i) in recentUpdates" :key="i" class="update-item">
              <el-tag size="small" :type="item.tagType">{{ item.type }}</el-tag>
              <span class="update-name">{{ item.name }}</span>
              <span class="update-time">{{ item.time }}</span>
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

const barChartRef = ref(null)
const wordCloudRef = ref(null)
let barChart = null
let wordCloud = null

const metrics = [
  { label: '总小说数', value: '12,580', icon: 'Reading', color: 'linear-gradient(135deg, #667eea, #764ba2)' },
  { label: '今日更新', value: '328', icon: 'DocumentAdd', color: 'linear-gradient(135deg, #43e97b, #38f9d7)' },
  { label: '活跃用户', value: '5,621', icon: 'User', color: 'linear-gradient(135deg, #fa709a, #fee140)' },
  { label: '平均评分', value: '8.2', icon: 'Star', color: 'linear-gradient(135deg, #a18cd1, #fbc2eb)' }
]

const quickEntries = [
  { title: '书籍分析', icon: 'DataAnalysis', color: '#409eff', path: '/book/keyword' },
  { title: '情感分析', icon: 'ChatDotSquare', color: '#67c23a', path: '/sentiment/classify' },
  { title: '智能推荐', icon: 'MagicStick', color: '#e6a23c', path: '/recommend/hot' },
  { title: '市场趋势', icon: 'TrendCharts', color: '#f56c6c', path: '/trend/type' }
]

const hotNovels = [
  { name: '斗破苍穹', heat: '98,523' },
  { name: '完美世界', heat: '87,412' },
  { name: '遮天', heat: '76,891' },
  { name: '诡秘之主', heat: '65,234' },
  { name: '大奉打更人', heat: '54,876' }
]

const recentUpdates = [
  { name: '深海余烬 更新至第892章', type: '玄幻', tagType: '', time: '5分钟前' },
  { name: '道诡异仙 更新至第1203章', type: '仙侠', tagType: 'success', time: '12分钟前' },
  { name: '夜的命名术 更新至第756章', type: '都市', tagType: 'warning', time: '30分钟前' },
  { name: '家族修仙 更新至第445章', type: '仙侠', tagType: 'success', time: '1小时前' },
  { name: '星门 更新至第621章', type: '科幻', tagType: 'danger', time: '2小时前' }
]

function initBarChart() {
  if (!barChartRef.value) return
  barChart = echarts.init(barChartRef.value)
  barChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 80, right: 30, top: 20, bottom: 30 },
    xAxis: { type: 'value' },
    yAxis: {
      type: 'category',
      data: ['武侠', '言情', '悬疑', '历史', '科幻', '仙侠', '都市', '玄幻'],
      axisLabel: { fontSize: 13 }
    },
    series: [{
      type: 'bar',
      data: [420, 680, 750, 890, 1250, 1580, 2100, 3200],
      barWidth: 18,
      itemStyle: {
        borderRadius: [0, 4, 4, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#409eff' },
          { offset: 1, color: '#66b1ff' }
        ])
      }
    }]
  })
}

function initWordCloud() {
  if (!wordCloudRef.value) return
  wordCloud = echarts.init(wordCloudRef.value)
  const words = [
    { name: '穿越', value: 1200 }, { name: '重生', value: 1100 },
    { name: '系统', value: 980 }, { name: '修仙', value: 950 },
    { name: '异能', value: 880 }, { name: '豪门', value: 760 },
    { name: '末日', value: 720 }, { name: '宫斗', value: 680 },
    { name: '热血', value: 650 }, { name: '冒险', value: 620 },
    { name: '校园', value: 580 }, { name: '都市', value: 560 },
    { name: '升级', value: 540 }, { name: '复仇', value: 500 },
    { name: '星际', value: 480 }, { name: '灵异', value: 450 },
    { name: '甜宠', value: 430 }, { name: '权谋', value: 410 },
    { name: '战争', value: 390 }, { name: '商战', value: 370 }
  ]
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
  initBarChart()
  initWordCloud()
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
  height: 320px;
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
