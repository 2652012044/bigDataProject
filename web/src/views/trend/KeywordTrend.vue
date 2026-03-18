<template>
  <div class="keyword-trend-page">
    <div class="page-header">
      <h2 class="page-title">关键词趋势</h2>
      <p class="page-desc">追踪小说领域热门关键词的搜索热度变化，发现新兴趋势</p>
    </div>

    <div class="card-box search-card">
      <div class="search-bar">
        <el-input
          v-model="keywordInput"
          placeholder="输入关键词添加到对比..."
          size="large"
          class="search-input"
          @keyup.enter="addKeyword"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" size="large" @click="addKeyword">
          添加对比
        </el-button>
      </div>
      <div class="keyword-tags">
        <el-tag
          v-for="keyword in activeKeywords"
          :key="keyword"
          closable
          :color="keywordColorMap[keyword]"
          effect="dark"
          class="keyword-tag"
          @close="removeKeyword(keyword)"
        >
          {{ keyword }}
        </el-tag>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="17">
        <div class="card-box">
          <div class="card-header">
            <span class="card-title">关键词热度趋势</span>
            <div class="card-actions">
              <el-radio-group v-model="timeRange" size="small">
                <el-radio-button value="6m">近6月</el-radio-button>
                <el-radio-button value="12m">近12月</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <div ref="trendChartRef" class="chart-container"></div>
        </div>
      </el-col>

      <el-col :span="7">
        <div class="card-box emerging-card">
          <div class="card-header">
            <span class="card-title">新兴关键词</span>
            <el-tag size="small" type="warning">实时</el-tag>
          </div>
          <div class="emerging-list">
            <div
              v-for="(item, index) in emergingKeywords"
              :key="item.keyword"
              class="emerging-item"
              @click="addEmergingKeyword(item.keyword)"
            >
              <div class="emerging-rank" :class="getRankClass(index)">
                {{ index + 1 }}
              </div>
              <div class="emerging-info">
                <el-tag
                  size="small"
                  effect="plain"
                  class="emerging-tag"
                >
                  {{ item.keyword }}
                </el-tag>
              </div>
              <div class="emerging-trend" :class="item.change >= 0 ? 'trend-up' : 'trend-down'">
                <span class="trend-arrow">{{ item.change >= 0 ? '▲' : '▼' }}</span>
                <span class="trend-value">{{ Math.abs(item.change) }}%</span>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const trendChartRef = ref(null)
let trendChart = null
const timeRange = ref('12m')
const keywordInput = ref('')

const months = [
  '1月', '2月', '3月', '4月', '5月', '6月',
  '7月', '8月', '9月', '10月', '11月', '12月'
]

const allKeywordData = {
  穿越: [78, 82, 85, 80, 88, 92, 95, 90, 87, 93, 96, 100],
  重生: [65, 68, 72, 75, 80, 85, 82, 88, 92, 95, 90, 94],
  系统: [52, 55, 60, 65, 70, 72, 78, 82, 85, 80, 88, 91],
  末日: [30, 35, 38, 42, 48, 55, 62, 68, 75, 82, 88, 95],
  无敌: [40, 42, 45, 50, 48, 52, 55, 60, 58, 62, 65, 68],
  修仙: [70, 72, 68, 75, 78, 80, 76, 82, 85, 88, 84, 90],
  赘婿: [55, 60, 65, 58, 52, 48, 45, 42, 40, 38, 35, 32],
  团宠: [25, 28, 35, 42, 50, 55, 60, 65, 70, 75, 80, 85],
  直播: [35, 38, 42, 48, 52, 58, 62, 65, 70, 72, 78, 82],
  副本: [20, 25, 30, 35, 42, 48, 55, 60, 65, 72, 78, 86]
}

const colorPalette = [
  '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
  '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#48b8d0'
]

const activeKeywords = ref(['穿越', '重生', '系统', '末日'])

const keywordColorMap = ref({})

const updateColorMap = () => {
  const map = {}
  activeKeywords.value.forEach((kw, i) => {
    map[kw] = colorPalette[i % colorPalette.length]
  })
  keywordColorMap.value = map
}

updateColorMap()

const emergingKeywords = ref([
  { keyword: '末日', change: 26.5 },
  { keyword: '团宠', change: 22.3 },
  { keyword: '副本', change: 19.8 },
  { keyword: '直播', change: 15.2 },
  { keyword: '无限流', change: 14.6 },
  { keyword: '规则怪谈', change: 12.8 },
  { keyword: '星际', change: 10.5 },
  { keyword: '种田', change: 8.2 },
  { keyword: '赘婿', change: -8.6 },
  { keyword: '宫斗', change: -12.3 }
])

const getRankClass = (index) => {
  if (index === 0) return 'rank-1'
  if (index === 1) return 'rank-2'
  if (index === 2) return 'rank-3'
  return ''
}

const addKeyword = () => {
  const kw = keywordInput.value.trim()
  if (!kw) return

  if (activeKeywords.value.includes(kw)) {
    ElMessage.warning(`"${kw}" 已在对比列表中`)
    keywordInput.value = ''
    return
  }

  if (activeKeywords.value.length >= 6) {
    ElMessage.warning('最多同时对比 6 个关键词')
    return
  }

  if (!allKeywordData[kw]) {
    allKeywordData[kw] = months.map(() => Math.floor(Math.random() * 80 + 20))
  }

  activeKeywords.value.push(kw)
  keywordInput.value = ''
  updateColorMap()
  updateChart()
}

const removeKeyword = (keyword) => {
  activeKeywords.value = activeKeywords.value.filter((k) => k !== keyword)
  updateColorMap()
  updateChart()
}

const addEmergingKeyword = (keyword) => {
  if (activeKeywords.value.includes(keyword)) {
    ElMessage.info(`"${keyword}" 已在对比列表中`)
    return
  }

  if (activeKeywords.value.length >= 6) {
    ElMessage.warning('最多同时对比 6 个关键词')
    return
  }

  if (!allKeywordData[keyword]) {
    allKeywordData[keyword] = months.map(() => Math.floor(Math.random() * 80 + 20))
  }

  activeKeywords.value.push(keyword)
  updateColorMap()
  updateChart()
  ElMessage.success(`已添加 "${keyword}" 到对比`)
}

const buildChartOption = () => {
  const isHalf = timeRange.value === '6m'
  const xData = isHalf ? months.slice(6) : months

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: '#e4e7ed',
      textStyle: { color: '#303133' },
      axisPointer: {
        type: 'line',
        lineStyle: { color: '#dcdfe6', type: 'dashed' }
      }
    },
    legend: {
      data: activeKeywords.value,
      top: 8,
      textStyle: { color: '#606266' }
    },
    grid: {
      left: 50,
      right: 30,
      top: 50,
      bottom: 35
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xData,
      axisLine: { lineStyle: { color: '#dcdfe6' } },
      axisLabel: { color: '#606266' }
    },
    yAxis: {
      type: 'value',
      name: '搜索热度',
      nameTextStyle: { color: '#909399' },
      max: 100,
      min: 0,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f0f2f5' } },
      axisLabel: {
        color: '#606266',
        formatter: '{value}'
      }
    },
    series: activeKeywords.value.map((keyword) => {
      const fullData = allKeywordData[keyword] || []
      const seriesData = isHalf ? fullData.slice(6) : fullData
      const color = keywordColorMap.value[keyword]

      return {
        name: keyword,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        showSymbol: false,
        lineStyle: { width: 2.5 },
        itemStyle: { color },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: color + '30' },
            { offset: 1, color: color + '05' }
          ])
        },
        emphasis: {
          focus: 'series',
          showSymbol: true,
          itemStyle: { borderWidth: 3 }
        },
        data: seriesData
      }
    })
  }
}

const updateChart = () => {
  if (trendChart) {
    trendChart.setOption(buildChartOption(), true)
  }
}

const handleResize = () => {
  trendChart?.resize()
}

watch(timeRange, () => {
  updateChart()
})

onMounted(() => {
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
    trendChart.setOption(buildChartOption())
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  trendChart = null
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.keyword-trend-page {
  padding: $spacing-lg;
  background: $bg-page;
  min-height: calc(100vh - #{$top-nav-height});
}

.page-header {
  margin-bottom: $spacing-lg;

  .page-title {
    font-size: 22px;
    font-weight: 700;
    color: $text-primary;
    margin: 0 0 6px 0;
  }

  .page-desc {
    font-size: 13px;
    color: $text-secondary;
    margin: 0;
  }
}

.card-box {
  background: $bg-white;
  border-radius: $border-radius-md;
  box-shadow: $box-shadow-light;
  padding: $spacing-lg;
  margin-bottom: $spacing-md;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-md;

  .card-title {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
  }
}

.search-card {
  .search-bar {
    display: flex;
    gap: 12px;
    margin-bottom: $spacing-md;

    .search-input {
      flex: 1;
    }
  }

  .keyword-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    min-height: 32px;

    .keyword-tag {
      border: none;
      font-size: 13px;
      font-weight: 500;
      letter-spacing: 1px;
    }
  }
}

.chart-container {
  width: 100%;
  height: 420px;
}

.emerging-card {
  .emerging-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .emerging-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 12px;
    border-radius: $border-radius-sm;
    background: $bg-color;
    cursor: pointer;
    transition: all 0.25s ease;

    &:hover {
      background: #edf0f5;
      transform: translateX(4px);
    }
  }

  .emerging-rank {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    color: #fff;
    background: $info-color;
    flex-shrink: 0;

    &.rank-1 {
      background: linear-gradient(135deg, #f56c6c, #e6394a);
    }

    &.rank-2 {
      background: linear-gradient(135deg, #e6a23c, #d48806);
    }

    &.rank-3 {
      background: linear-gradient(135deg, #409eff, #3375b9);
    }
  }

  .emerging-info {
    flex: 1;

    .emerging-tag {
      font-size: 13px;
    }
  }

  .emerging-trend {
    display: flex;
    align-items: center;
    gap: 3px;
    flex-shrink: 0;
    font-size: 12px;
    font-weight: 600;

    &.trend-up {
      color: $success-color;

      .trend-arrow {
        font-size: 10px;
      }
    }

    &.trend-down {
      color: $danger-color;

      .trend-arrow {
        font-size: 10px;
      }
    }
  }
}
</style>
