<template>
  <div class="hotspot-analysis">
    <h2 class="page-title">热点分析</h2>

    <el-row :gutter="20">
      <el-col :span="14">
        <div class="card-box">
          <h3 class="card-title">热门讨论词云</h3>
          <div ref="wordcloudRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :span="10">
        <div class="card-box topic-card">
          <h3 class="card-title">热门话题榜</h3>
          <div class="topic-list">
            <el-card v-for="(topic, index) in topicList" :key="index" shadow="hover" class="topic-item">
              <div class="topic-header">
                <span :class="['topic-rank', { 'rank-hot': index < 3 }]">{{ index + 1 }}</span>
                <span class="topic-title">{{ topic.title }}</span>
                <el-tag size="small" :type="index < 3 ? 'danger' : index < 6 ? 'warning' : 'info'" effect="plain">{{ topic.tag }}</el-tag>
              </div>
              <div class="topic-meta">
                <span class="heat-label">评论数: {{ topic.heat }}</span>
                <span class="novel-count">分类: {{ topic.tag }}</span>
              </div>
              <el-progress :percentage="topic.heatPercent" :stroke-width="10" :color="getHeatColor(topic.heatPercent)" :show-text="false" />
            </el-card>
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

const wordcloudRef = ref(null)
let wordcloudChart = null
const topicList = ref([])

const getHeatColor = (percent) => {
  if (percent >= 80) return '#f56c6c'
  if (percent >= 60) return '#e6a23c'
  if (percent >= 40) return '#409eff'
  return '#909399'
}

async function loadWordcloud() {
  try {
    const res = await request.get('/sentiment/hotspot/wordcloud')
    initWordcloud(res.data || [])
  } catch (e) {
    initWordcloud([])
  }
}

async function loadTopics() {
  try {
    const res = await request.get('/sentiment/hotspot/topics')
    topicList.value = res.data || []
  } catch (e) { /* keep empty */ }
}

const initWordcloud = (data) => {
  if (!wordcloudRef.value) return
  wordcloudChart = echarts.init(wordcloudRef.value)
  wordcloudChart.setOption({
    tooltip: { show: true, formatter: params => `${params.name}: ${params.value}` },
    series: [{
      type: 'wordCloud', shape: 'circle', left: 'center', top: 'center',
      width: '90%', height: '90%', sizeRange: [14, 56], rotationRange: [-45, 45],
      rotationStep: 15, gridSize: 10, drawOutOfBound: false, layoutAnimation: true,
      textStyle: {
        fontFamily: 'Microsoft YaHei, sans-serif', fontWeight: 'bold',
        color: () => {
          const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#7c4dff', '#00bcd4', '#ff5722', '#8bc34a', '#3f51b5']
          return colors[Math.floor(Math.random() * colors.length)]
        }
      },
      emphasis: { textStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.25)' } },
      data
    }]
  })
}

const handleResize = () => { wordcloudChart?.resize() }

onMounted(() => {
  loadWordcloud()
  loadTopics()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  wordcloudChart?.dispose()
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.hotspot-analysis { padding: $spacing-lg; }
.page-title { font-size: 22px; font-weight: 600; color: $text-primary; margin-bottom: $spacing-lg; }
.card-box { background: $bg-white; border-radius: $border-radius-md; box-shadow: $box-shadow-light; padding: $spacing-lg; margin-bottom: $spacing-lg; }
.card-title { font-size: 16px; font-weight: 600; color: $text-primary; margin-bottom: $spacing-md; padding-left: $spacing-sm; border-left: 3px solid $primary-color; }
.chart-container { width: 100%; height: 520px; }
.topic-card {
  max-height: 580px; overflow-y: auto;
  &::-webkit-scrollbar { width: 6px; }
  &::-webkit-scrollbar-thumb { background: $border-color; border-radius: 3px; }
}
.topic-list { display: flex; flex-direction: column; gap: $spacing-sm; }
.topic-item {
  :deep(.el-card__body) { padding: 14px 16px; }
  .topic-header { display: flex; align-items: center; gap: $spacing-sm; margin-bottom: $spacing-sm; }
  .topic-rank {
    display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px;
    border-radius: 50%; font-size: 12px; font-weight: 700; color: $text-secondary; background: $bg-color; flex-shrink: 0;
    &.rank-hot { color: #fff; background: linear-gradient(135deg, #f56c6c 0%, #e6a23c 100%); }
  }
  .topic-title { flex: 1; font-size: 14px; font-weight: 600; color: $text-primary; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .topic-meta {
    display: flex; justify-content: space-between; margin-bottom: $spacing-sm; font-size: 12px; color: $text-secondary;
    .heat-label { color: $danger-color; font-weight: 500; }
  }
}
</style>
