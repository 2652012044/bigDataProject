<template>
  <div class="heat-trend-page">
    <div class="page-header">
      <h2 class="page-title">热度趋势</h2>
      <p class="page-desc">对比不同小说的热度数据，洞察市场热点走向</p>
    </div>

    <el-alert v-if="notice" :title="notice" type="info" show-icon :closable="false" style="margin-bottom: 16px;" />

    <div class="card-box">
      <div class="card-header">
        <span class="card-title">热度排行对比</span>
      </div>
      <div ref="barChartRef" class="chart-container"></div>
    </div>

    <div class="card-box">
      <div class="card-header">
        <span class="card-title">热度数据明细</span>
      </div>
      <el-table :data="bookData" stripe style="width: 100%" :header-cell-style="{ background: '#f5f7fa', color: '#303133', fontWeight: 600 }">
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column prop="name" label="小说名" min-width="140">
          <template #default="{ row }">
            <span class="novel-name">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="readCount" label="阅读量" width="140" align="center" sortable>
          <template #default="{ row }">
            <span class="heat-value">{{ Number(row.readCount).toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="评分" width="100" align="center" sortable />
        <el-table-column prop="category" label="分类" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ row.category || '其他' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="commentTotal" label="评论数" width="120" align="center" sortable />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import request from '@/api/index'

const barChartRef = ref(null)
let barChart = null
const bookData = ref([])
const notice = ref('')

async function loadData() {
  try {
    const res = await request.get('/trend/heat')
    const data = res.data || {}
    bookData.value = data.books || []
    notice.value = data.notice || ''
    initChart()
  } catch (e) { /* keep empty */ }
}

function initChart() {
  if (!barChartRef.value || bookData.value.length === 0) return
  barChart = echarts.init(barChartRef.value)

  const names = bookData.value.map(b => b.name)
  const reads = bookData.value.map(b => b.readCount)
  const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#48b8d0']

  barChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: params => `${params[0].name}<br/>阅读量：${Number(params[0].value).toLocaleString()}` },
    grid: { left: 120, right: 40, top: 10, bottom: 10 },
    xAxis: { type: 'value', show: false },
    yAxis: { type: 'category', data: names.reverse(), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { fontSize: 13, color: '#606266' } },
    series: [{
      type: 'bar', barWidth: 18,
      data: reads.reverse().map((v, i) => ({
        value: v,
        itemStyle: { borderRadius: [0, 4, 4, 0], color: colors[i % colors.length] }
      })),
      label: { show: true, position: 'right', fontSize: 12, color: '#909399', formatter: params => Number(params.value).toLocaleString() }
    }]
  })
}

const handleResize = () => { barChart?.resize() }
onMounted(() => { loadData(); window.addEventListener('resize', handleResize) })
onUnmounted(() => { window.removeEventListener('resize', handleResize); barChart?.dispose() })
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.heat-trend-page { padding: $spacing-lg; background: $bg-page; min-height: calc(100vh - #{$top-nav-height}); }
.page-header { margin-bottom: $spacing-lg; .page-title { font-size: 22px; font-weight: 700; color: $text-primary; margin: 0 0 6px 0; } .page-desc { font-size: 13px; color: $text-secondary; margin: 0; } }
.card-box { background: $bg-white; border-radius: $border-radius-md; box-shadow: $box-shadow-light; padding: $spacing-lg; margin-bottom: $spacing-md; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: $spacing-md; .card-title { font-size: 16px; font-weight: 600; color: $text-primary; } }
.chart-container { width: 100%; height: 400px; }
.novel-name { font-weight: 500; color: $text-primary; }
.heat-value { font-weight: 600; color: $text-primary; font-size: 14px; }
</style>
