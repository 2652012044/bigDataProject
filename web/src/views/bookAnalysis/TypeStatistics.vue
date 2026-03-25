<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">类型统计</h2>
      <p class="page-desc">小说类型分布与详细统计分析</p>
    </div>

    <el-row :gutter="20">
      <el-col :span="24">
        <div class="card-box">
          <div class="card-box-header">
            <span class="card-box-title">各类型小说数量分布</span>
            <div class="chart-actions">
              <el-radio-group v-model="chartMode" size="small">
                <el-radio-button value="bar">柱状图</el-radio-button>
                <el-radio-button value="radar">雷达图</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <div ref="barChartRef" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="16">
        <div class="card-box">
          <div class="card-box-header">
            <span class="card-box-title">当前类型分布 (矩形树图)</span>
          </div>
          <div ref="treemapRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="card-box summary-box">
          <div class="card-box-header">
            <span class="card-box-title">类型数据汇总</span>
          </div>
          <div class="summary-list">
            <div v-for="(item, index) in typesSummary" :key="item.name" class="summary-item">
              <div class="summary-rank" :style="{ background: typeColors[index % typeColors.length] }">{{ index + 1 }}</div>
              <div class="summary-info">
                <div class="summary-name">{{ item.name }}</div>
                <el-progress :percentage="item.percent" :color="typeColors[index % typeColors.length]" :stroke-width="8" :show-text="false" />
              </div>
              <div class="summary-values">
                <span class="summary-count">{{ item.count.toLocaleString() }}部</span>
                <span class="summary-percent">{{ item.percent }}%</span>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import request from '@/api/index'

const typeColors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#9b59b6', '#1abc9c', '#e67e22', '#3f51b5', '#00bcd4', '#ff5722', '#8bc34a', '#795548', '#607d8b', '#cddc39', '#ff9800']

const barChartRef = ref(null)
const treemapRef = ref(null)
let barChart = null
let treemapChart = null
const chartMode = ref('bar')

const typeList = ref([])
const typesSummary = ref([])
let grandTotal = 0

async function loadTypeStats() {
  try {
    const res = await request.get('/analysis/type-stats')
    const data = res.data || {}
    typeList.value = data.types || []
    grandTotal = data.totalBooks || 0

    typesSummary.value = typeList.value.map(t => ({
      name: t.name,
      count: t.count,
      percent: grandTotal > 0 ? parseFloat(((t.count / grandTotal) * 100).toFixed(1)) : 0
    }))

    initBarChart()
    initTreemap()
  } catch (e) { /* keep empty */ }
}

function initBarChart() {
  if (!barChartRef.value || typeList.value.length === 0) return
  barChart = echarts.init(barChartRef.value)
  updateBarChart()
}

function updateBarChart() {
  if (!barChart) return
  const names = typeList.value.map(t => t.name)
  const counts = typeList.value.map(t => t.count)

  if (chartMode.value === 'radar') {
    const maxVal = Math.max(...counts) * 1.2
    barChart.setOption({
      tooltip: {},
      radar: {
        indicator: names.map(n => ({ name: n, max: maxVal })),
        radius: '65%',
        axisName: { color: '#606266', fontSize: 12 }
      },
      series: [{ type: 'radar', data: [{ value: counts, name: '书籍数量', areaStyle: { opacity: 0.3 }, lineStyle: { width: 2 }, itemStyle: { color: '#409eff' } }] }]
    }, true)
  } else {
    barChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: params => `${params[0].name}：${params[0].value} 部` },
      grid: { left: '3%', right: '4%', bottom: '3%', top: 20, containLabel: true },
      xAxis: { type: 'category', data: names, axisLabel: { fontSize: 12, rotate: names.length > 10 ? 30 : 0 } },
      yAxis: { type: 'value', name: '小说数量', axisLabel: { fontSize: 12 }, splitLine: { lineStyle: { type: 'dashed', color: '#e4e7ed' } } },
      series: [{
        type: 'bar', barWidth: '50%',
        data: counts.map((v, i) => ({
          value: v,
          itemStyle: { color: typeColors[i % typeColors.length], borderRadius: [4, 4, 0, 0] }
        })),
        label: { show: true, position: 'top', fontSize: 11, color: '#909399' }
      }]
    }, true)
  }
}

function initTreemap() {
  if (!treemapRef.value || typeList.value.length === 0) return
  treemapChart = echarts.init(treemapRef.value)

  const treemapData = typeList.value.map((t, i) => ({
    name: t.name, value: t.count,
    itemStyle: { color: typeColors[i % typeColors.length], borderColor: '#fff', borderWidth: 2 }
  }))

  treemapChart.setOption({
    tooltip: { formatter: params => {
      const percent = grandTotal > 0 ? ((params.value / grandTotal) * 100).toFixed(1) : 0
      return `<div style="font-weight:bold;margin-bottom:4px;">${params.name}</div><div>小说数量: ${params.value.toLocaleString()} 部</div><div>占比: ${percent}%</div>`
    }},
    series: [{
      type: 'treemap', width: '95%', height: '90%', top: '5%', left: '2.5%',
      roam: false, nodeClick: false, breadcrumb: { show: false },
      label: {
        show: true,
        formatter: params => {
          const percent = grandTotal > 0 ? ((params.value / grandTotal) * 100).toFixed(1) : 0
          return `{name|${params.name}}\n{value|${params.value.toLocaleString()}部}\n{percent|${percent}%}`
        },
        rich: {
          name: { fontSize: 16, fontWeight: 'bold', color: '#fff', lineHeight: 28 },
          value: { fontSize: 13, color: 'rgba(255,255,255,0.9)', lineHeight: 22 },
          percent: { fontSize: 20, fontWeight: 'bold', color: '#fff', lineHeight: 28 }
        },
        align: 'center', verticalAlign: 'middle'
      },
      itemStyle: { borderRadius: 6, gapWidth: 3 },
      emphasis: { itemStyle: { shadowBlur: 15, shadowColor: 'rgba(0, 0, 0, 0.3)' } },
      levels: [{ itemStyle: { borderColor: '#fff', borderWidth: 3, gapWidth: 3 } }],
      data: treemapData
    }]
  })
}

function handleResize() { barChart?.resize(); treemapChart?.resize() }
watch(chartMode, () => { updateBarChart() })

onMounted(() => { loadTypeStats(); window.addEventListener('resize', handleResize) })
onUnmounted(() => { window.removeEventListener('resize', handleResize); barChart?.dispose(); treemapChart?.dispose() })
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.page-container { padding: $spacing-lg; min-height: 100%; }
.page-header { margin-bottom: $spacing-lg; .page-title { font-size: 22px; font-weight: 600; color: $text-primary; margin: 0 0 $spacing-xs 0; } .page-desc { font-size: 14px; color: $text-secondary; margin: 0; } }
.card-box {
  background: $bg-white; border-radius: $border-radius-md; box-shadow: $box-shadow-light; padding: $spacing-lg; margin-bottom: $spacing-lg;
  .card-box-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: $spacing-md; .card-box-title { font-size: 16px; font-weight: 600; color: $text-primary; } }
}
.chart-container { width: 100%; height: 420px; }
.chart-actions { display: flex; align-items: center; gap: $spacing-sm; }
.summary-box {
  .summary-list { display: flex; flex-direction: column; gap: $spacing-md; }
  .summary-item { display: flex; align-items: center; gap: $spacing-md; padding: $spacing-sm 0;
    .summary-rank { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 13px; font-weight: 600; flex-shrink: 0; }
    .summary-info { flex: 1; min-width: 0; .summary-name { font-size: 14px; font-weight: 500; color: $text-primary; margin-bottom: $spacing-xs; } }
    .summary-values { display: flex; flex-direction: column; align-items: flex-end; flex-shrink: 0; .summary-count { font-size: 14px; font-weight: 600; color: $text-primary; } .summary-percent { font-size: 12px; color: $text-secondary; margin-top: 2px; } }
  }
}
</style>
