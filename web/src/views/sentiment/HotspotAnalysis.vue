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
            <el-card
              v-for="(topic, index) in topicList"
              :key="index"
              shadow="hover"
              class="topic-item"
            >
              <div class="topic-header">
                <span :class="['topic-rank', { 'rank-hot': index < 3 }]">{{ index + 1 }}</span>
                <span class="topic-title">{{ topic.title }}</span>
                <el-tag size="small" :type="topic.tagType" effect="plain">{{ topic.tag }}</el-tag>
              </div>
              <div class="topic-meta">
                <span class="heat-label">热度值: {{ topic.heat }}</span>
                <span class="novel-count">相关小说: {{ topic.novelCount }} 部</span>
              </div>
              <el-progress
                :percentage="topic.heatPercent"
                :stroke-width="10"
                :color="getHeatColor(topic.heatPercent)"
                :show-text="false"
              />
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

const wordcloudRef = ref(null)
let wordcloudChart = null

const wordcloudData = [
  { name: '剧情反转', value: 1680 },
  { name: '人物塑造', value: 1520 },
  { name: '世界观', value: 1430 },
  { name: '战斗场面', value: 1350 },
  { name: '感情线', value: 1280 },
  { name: '伏笔回收', value: 1190 },
  { name: '节奏把控', value: 1100 },
  { name: '文笔优美', value: 1040 },
  { name: '逻辑缺陷', value: 960 },
  { name: '水字数', value: 890 },
  { name: '设定新颖', value: 870 },
  { name: '主角光环', value: 830 },
  { name: '配角出彩', value: 780 },
  { name: '升级体系', value: 750 },
  { name: '反派智商', value: 720 },
  { name: '伏笔埋线', value: 690 },
  { name: '烂尾预警', value: 670 },
  { name: '金手指', value: 640 },
  { name: '热血燃文', value: 610 },
  { name: '打脸爽文', value: 590 },
  { name: '细节描写', value: 560 },
  { name: '情感共鸣', value: 530 },
  { name: '节奏拖沓', value: 500 },
  { name: '高开低走', value: 480 },
  { name: '完结神作', value: 450 },
  { name: '弃书率高', value: 420 },
  { name: '悬念设置', value: 400 },
  { name: '日常描写', value: 370 },
  { name: '后宫争斗', value: 340 },
  { name: '无敌流', value: 310 }
]

const topicList = [
  { title: '剧情反转引发读者热议', heat: 9680, heatPercent: 97, novelCount: 42, tag: '热门', tagType: 'danger' },
  { title: '人物塑造深度对比分析', heat: 8750, heatPercent: 88, novelCount: 38, tag: '热门', tagType: 'danger' },
  { title: '年度最佳世界观设定评选', heat: 8120, heatPercent: 81, novelCount: 35, tag: '热门', tagType: 'danger' },
  { title: '经典战斗场面回顾盘点', heat: 7340, heatPercent: 73, novelCount: 31, tag: '推荐', tagType: 'warning' },
  { title: '最佳感情线发展走向投票', heat: 6850, heatPercent: 69, novelCount: 28, tag: '推荐', tagType: 'warning' },
  { title: '伏笔回收最惊艳的小说', heat: 6230, heatPercent: 62, novelCount: 25, tag: '推荐', tagType: 'warning' },
  { title: '节奏把控与阅读体验讨论', heat: 5410, heatPercent: 54, novelCount: 22, tag: '一般', tagType: 'info' },
  { title: '文笔优美小说推荐合集', heat: 4760, heatPercent: 48, novelCount: 19, tag: '一般', tagType: 'info' },
  { title: '逻辑缺陷吐槽大会', heat: 4120, heatPercent: 41, novelCount: 16, tag: '一般', tagType: 'info' },
  { title: '水字数与更新质量辩论', heat: 3580, heatPercent: 36, novelCount: 13, tag: '新话题', tagType: '' }
]

const getHeatColor = (percent) => {
  if (percent >= 80) return '#f56c6c'
  if (percent >= 60) return '#e6a23c'
  if (percent >= 40) return '#409eff'
  return '#909399'
}

const initWordcloud = () => {
  wordcloudChart = echarts.init(wordcloudRef.value)
  const option = {
    tooltip: {
      show: true,
      formatter: (params) => `${params.name}: ${params.value}`
    },
    series: [
      {
        type: 'wordCloud',
        shape: 'circle',
        left: 'center',
        top: 'center',
        width: '90%',
        height: '90%',
        sizeRange: [14, 56],
        rotationRange: [-45, 45],
        rotationStep: 15,
        gridSize: 10,
        drawOutOfBound: false,
        layoutAnimation: true,
        textStyle: {
          fontFamily: 'Microsoft YaHei, sans-serif',
          fontWeight: 'bold',
          color: () => {
            const colors = [
              '#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399',
              '#7c4dff', '#00bcd4', '#ff5722', '#8bc34a', '#3f51b5'
            ]
            return colors[Math.floor(Math.random() * colors.length)]
          }
        },
        emphasis: {
          textStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.25)'
          }
        },
        data: wordcloudData
      }
    ]
  }
  wordcloudChart.setOption(option)
}

const handleResize = () => {
  wordcloudChart?.resize()
}

onMounted(() => {
  initWordcloud()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  wordcloudChart?.dispose()
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.hotspot-analysis {
  padding: $spacing-lg;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: $spacing-lg;
}

.card-box {
  background: $bg-white;
  border-radius: $border-radius-md;
  box-shadow: $box-shadow-light;
  padding: $spacing-lg;
  margin-bottom: $spacing-lg;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: $spacing-md;
  padding-left: $spacing-sm;
  border-left: 3px solid $primary-color;
}

.chart-container {
  width: 100%;
  height: 520px;
}

.topic-card {
  max-height: 580px;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background: $border-color;
    border-radius: 3px;
  }
}

.topic-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}

.topic-item {
  :deep(.el-card__body) {
    padding: 14px 16px;
  }

  .topic-header {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    margin-bottom: $spacing-sm;
  }

  .topic-rank {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    font-size: 12px;
    font-weight: 700;
    color: $text-secondary;
    background: $bg-color;
    flex-shrink: 0;

    &.rank-hot {
      color: #fff;
      background: linear-gradient(135deg, #f56c6c 0%, #e6a23c 100%);
    }
  }

  .topic-title {
    flex: 1;
    font-size: 14px;
    font-weight: 600;
    color: $text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .topic-meta {
    display: flex;
    justify-content: space-between;
    margin-bottom: $spacing-sm;
    font-size: 12px;
    color: $text-secondary;

    .heat-label {
      color: $danger-color;
      font-weight: 500;
    }
  }
}
</style>
