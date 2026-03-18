<template>
  <div class="heat-trend-page">
    <div class="page-header">
      <h2 class="page-title">热度趋势</h2>
      <p class="page-desc">对比不同小说的热度指数变化，洞察市场热点走向</p>
    </div>

    <div class="card-box filter-card">
      <el-row :gutter="16" align="middle">
        <el-col :span="18">
          <div class="filter-row">
            <span class="filter-label">选择小说：</span>
            <el-select
              v-model="selectedNovels"
              multiple
              collapse-tags
              collapse-tags-tooltip
              placeholder="请选择要对比的小说"
              style="width: 100%"
              @change="handleSelectionChange"
            >
              <el-option
                v-for="novel in allNovels"
                :key="novel"
                :label="novel"
                :value="novel"
              />
            </el-select>
          </div>
        </el-col>
        <el-col :span="6" style="text-align: right">
          <el-button type="primary" @click="handleSelectionChange">
            更新图表
          </el-button>
          <el-button @click="resetSelection">重置</el-button>
        </el-col>
      </el-row>
    </div>

    <div class="card-box">
      <div class="card-header">
        <span class="card-title">热度指数对比</span>
        <div class="card-actions">
          <el-radio-group v-model="timeRange" size="small">
            <el-radio-button value="half">近半年</el-radio-button>
            <el-radio-button value="full">全年</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      <div ref="lineChartRef" class="chart-container"></div>
    </div>

    <div class="card-box">
      <div class="card-header">
        <span class="card-title">热度数据明细</span>
        <el-tag size="small" type="info">{{ currentMonth }}</el-tag>
      </div>
      <el-table
        :data="tableData"
        stripe
        style="width: 100%"
        :header-cell-style="{ background: '#f5f7fa', color: '#303133', fontWeight: 600 }"
      >
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column prop="name" label="小说名" min-width="140">
          <template #default="{ row }">
            <div class="novel-name-cell">
              <span
                class="color-dot"
                :style="{ background: row.color }"
              ></span>
              <span class="novel-name">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="currentHeat" label="本月热度" width="120" align="center">
          <template #default="{ row }">
            <span class="heat-value">{{ row.currentHeat.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="lastHeat" label="上月热度" width="120" align="center">
          <template #default="{ row }">
            <span class="heat-value-secondary">{{ row.lastHeat.toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="change" label="环比变化" width="120" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.change >= 0 ? 'success' : 'danger'"
              size="small"
            >
              {{ row.change >= 0 ? '+' : '' }}{{ row.change }}%
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="discussions" label="讨论数" width="120" align="center">
          <template #default="{ row }">
            <span>{{ row.discussions.toLocaleString() }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const lineChartRef = ref(null)
let lineChart = null
const timeRange = ref('full')
const currentMonth = '2025年12月'

const allNovels = ['斗破苍穹', '完美世界', '遮天', '诡秘之主', '大奉打更人']
const selectedNovels = ref(['斗破苍穹', '完美世界', '遮天'])

const defaultSelected = ['斗破苍穹', '完美世界', '遮天']

const months = [
  '1月', '2月', '3月', '4月', '5月', '6月',
  '7月', '8月', '9月', '10月', '11月', '12月'
]

const novelColors = {
  斗破苍穹: '#5470c6',
  完美世界: '#91cc75',
  遮天: '#fac858',
  诡秘之主: '#ee6666',
  大奉打更人: '#73c0de'
}

const novelData = {
  斗破苍穹: [8200, 8500, 8800, 9100, 9600, 10200, 10800, 11500, 12200, 12800, 13500, 14200],
  完美世界: [7100, 7400, 7200, 7800, 8200, 8600, 9200, 9800, 10500, 11000, 11800, 12300],
  遮天: [6800, 7000, 7300, 7100, 7500, 7900, 8400, 8800, 9200, 9600, 10200, 10800],
  诡秘之主: [9500, 9200, 9800, 10200, 10800, 11500, 12000, 12800, 13200, 13800, 14500, 15200],
  大奉打更人: [5500, 5800, 6200, 6800, 7200, 7800, 8500, 9000, 9500, 10200, 10800, 11500]
}

const tableData = computed(() =>
  allNovels.map((name) => {
    const data = novelData[name]
    const current = data[11]
    const last = data[10]
    const change = ((current - last) / last * 100).toFixed(1)
    return {
      name,
      color: novelColors[name],
      currentHeat: current,
      lastHeat: last,
      change: Number(change),
      discussions: Math.floor(current * 0.35 + Math.random() * 500)
    }
  })
)

const buildLineOption = () => {
  const isHalf = timeRange.value === 'half'
  const xData = isHalf ? months.slice(6) : months
  const filtered = selectedNovels.value.length > 0 ? selectedNovels.value : defaultSelected

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: '#e4e7ed',
      textStyle: { color: '#303133' },
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: filtered,
      top: 8,
      textStyle: { color: '#606266' }
    },
    grid: {
      left: 60,
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
      name: '热度指数',
      nameTextStyle: { color: '#909399' },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f0f2f5' } },
      axisLabel: { color: '#606266' }
    },
    series: filtered.map((name) => {
      const fullData = novelData[name]
      const seriesData = isHalf ? fullData.slice(6) : fullData
      return {
        name,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 7,
        lineStyle: { width: 2.5 },
        itemStyle: { color: novelColors[name] },
        emphasis: {
          focus: 'series',
          itemStyle: { borderWidth: 3 }
        },
        data: seriesData
      }
    })
  }
}

const handleSelectionChange = () => {
  if (lineChart) {
    lineChart.setOption(buildLineOption(), true)
  }
}

const resetSelection = () => {
  selectedNovels.value = [...defaultSelected]
  handleSelectionChange()
}

const handleResize = () => {
  lineChart?.resize()
}

watch(timeRange, () => {
  if (lineChart) {
    lineChart.setOption(buildLineOption(), true)
  }
})

onMounted(() => {
  if (lineChartRef.value) {
    lineChart = echarts.init(lineChartRef.value)
    lineChart.setOption(buildLineOption())
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  lineChart?.dispose()
  lineChart = null
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.heat-trend-page {
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

.filter-card {
  .filter-row {
    display: flex;
    align-items: center;
    gap: 12px;

    .filter-label {
      font-size: 14px;
      color: $text-regular;
      white-space: nowrap;
      font-weight: 500;
    }
  }
}

.chart-container {
  width: 100%;
  height: 400px;
}

.novel-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;

  .color-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .novel-name {
    font-weight: 500;
    color: $text-primary;
  }
}

.heat-value {
  font-weight: 600;
  color: $text-primary;
  font-size: 14px;
}

.heat-value-secondary {
  color: $text-secondary;
  font-size: 14px;
}

:deep(.el-table) {
  border-radius: $border-radius-sm;

  .el-table__row {
    transition: background 0.2s;
  }
}

:deep(.el-select) {
  .el-tag {
    max-width: 120px;
  }
}
</style>
