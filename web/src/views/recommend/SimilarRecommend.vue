<template>
  <div class="similar-recommend-page">
    <div class="page-header">
      <h2 class="page-title">相似推荐</h2>
      <p class="page-desc">选择一本小说，发现与之相似的作品关系网络</p>
    </div>

    <div class="search-bar">
      <el-select
        v-model="selectedNovel"
        filterable
        placeholder="搜索或选择一本小说"
        size="large"
        class="novel-select"
        @change="handleNovelChange"
      >
        <el-option
          v-for="novel in novelOptions"
          :key="novel.value"
          :label="novel.label"
          :value="novel.value"
        />
      </el-select>
    </div>

    <div class="content-layout">
      <div class="chart-panel">
        <div ref="chartRef" class="relation-chart"></div>
      </div>
      <div class="side-panel">
        <h3 class="panel-title">
          <el-icon><Connection /></el-icon>
          相似作品列表
        </h3>
        <div class="similar-list">
          <div
            class="similar-item"
            v-for="novel in currentSimilarNovels"
            :key="novel.id"
          >
            <div class="item-cover" :style="{ background: novel.coverColor }"></div>
            <div class="item-info">
              <div class="item-title">{{ novel.title }}</div>
              <div class="item-author">{{ novel.author }}</div>
              <div class="item-tags">
                <el-tag
                  v-for="tag in novel.tags"
                  :key="tag"
                  size="small"
                  effect="plain"
                  round
                >
                  {{ tag }}
                </el-tag>
              </div>
            </div>
            <div class="item-score">
              <el-progress
                type="dashboard"
                :percentage="novel.similarity"
                :width="56"
                :stroke-width="4"
                :color="getSimilarityColor(novel.similarity)"
              />
              <span class="score-label">相似度</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Connection } from '@element-plus/icons-vue'

const chartRef = ref(null)
let chartInstance = null

const coverColors = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)'
]

const novelOptions = [
  { value: 'dpcq', label: '斗破苍穹 - 天蚕土豆' },
  { value: 'frxxt', label: '凡人修仙传 - 忘语' },
  { value: 'gmzz', label: '诡秘之主 - 爱潜水的乌贼' },
  { value: 'zt', label: '遮天 - 辰东' },
  { value: 'qyn', label: '庆余年 - 猫腻' }
]

const selectedNovel = ref('dpcq')

const novelData = {
  dpcq: {
    center: { title: '斗破苍穹', author: '天蚕土豆' },
    similar: [
      { id: 1, title: '武动乾坤', author: '天蚕土豆', similarity: 92, tags: ['玄幻', '热血'], coverColor: coverColors[0] },
      { id: 2, title: '大主宰', author: '天蚕土豆', similarity: 88, tags: ['玄幻', '少年'], coverColor: coverColors[1] },
      { id: 3, title: '完美世界', author: '辰东', similarity: 79, tags: ['玄幻', '荒古'], coverColor: coverColors[2] },
      { id: 4, title: '帝霸', author: '厌笔萧生', similarity: 75, tags: ['玄幻', '无敌'], coverColor: coverColors[3] },
      { id: 5, title: '万相之王', author: '天蚕土豆', similarity: 85, tags: ['玄幻', '双主角'], coverColor: coverColors[4] },
      { id: 6, title: '伏天氏', author: '净无痕', similarity: 72, tags: ['玄幻', '天才'], coverColor: coverColors[5] }
    ]
  },
  frxxt: {
    center: { title: '凡人修仙传', author: '忘语' },
    similar: [
      { id: 7, title: '一世之尊', author: '爱潜水的乌贼', similarity: 85, tags: ['仙侠', '多主角'], coverColor: coverColors[0] },
      { id: 8, title: '剑来', author: '烽火戏诸侯', similarity: 80, tags: ['仙侠', '剑道'], coverColor: coverColors[1] },
      { id: 9, title: '我师兄实在太稳健了', author: '言归正传', similarity: 78, tags: ['仙侠', '稳健'], coverColor: coverColors[2] },
      { id: 10, title: '赤心巡天', author: '情何以甚', similarity: 76, tags: ['仙侠', '热血'], coverColor: coverColors[3] },
      { id: 11, title: '牧神记', author: '宅猪', similarity: 74, tags: ['仙侠', '少年'], coverColor: coverColors[4] },
      { id: 12, title: '道诡异仙', author: '狐尾的笔', similarity: 70, tags: ['仙侠', '诡异'], coverColor: coverColors[5] }
    ]
  },
  gmzz: {
    center: { title: '诡秘之主', author: '爱潜水的乌贼' },
    similar: [
      { id: 13, title: '宿命之环', author: '爱潜水的乌贼', similarity: 93, tags: ['奇幻', '诡秘'], coverColor: coverColors[0] },
      { id: 14, title: '道诡异仙', author: '狐尾的笔', similarity: 87, tags: ['仙侠', '诡异'], coverColor: coverColors[1] },
      { id: 15, title: '长夜余火', author: '爱潜水的乌贼', similarity: 82, tags: ['科幻', '冒险'], coverColor: coverColors[2] },
      { id: 16, title: '大奉打更人', author: '卖报小郎君', similarity: 78, tags: ['仙侠', '探案'], coverColor: coverColors[3] },
      { id: 17, title: '我有一座恐怖屋', author: '我会修空调', similarity: 73, tags: ['灵异', '恐怖'], coverColor: coverColors[4] },
      { id: 18, title: '一世之尊', author: '爱潜水的乌贼', similarity: 80, tags: ['仙侠', '多主角'], coverColor: coverColors[5] }
    ]
  },
  zt: {
    center: { title: '遮天', author: '辰东' },
    similar: [
      { id: 19, title: '完美世界', author: '辰东', similarity: 95, tags: ['玄幻', '远古'], coverColor: coverColors[0] },
      { id: 20, title: '深空彼岸', author: '辰东', similarity: 88, tags: ['科幻', '进化'], coverColor: coverColors[1] },
      { id: 21, title: '圣墟', author: '辰东', similarity: 91, tags: ['玄幻', '荒古'], coverColor: coverColors[2] },
      { id: 22, title: '斗破苍穹', author: '天蚕土豆', similarity: 79, tags: ['玄幻', '热血'], coverColor: coverColors[3] },
      { id: 23, title: '帝霸', author: '厌笔萧生', similarity: 77, tags: ['玄幻', '无敌'], coverColor: coverColors[4] },
      { id: 24, title: '星门', author: '辰东', similarity: 86, tags: ['科幻', '末世'], coverColor: coverColors[5] }
    ]
  },
  qyn: {
    center: { title: '庆余年', author: '猫腻' },
    similar: [
      { id: 25, title: '雪中悍刀行', author: '烽火戏诸侯', similarity: 89, tags: ['武侠', '文青'], coverColor: coverColors[0] },
      { id: 26, title: '剑来', author: '烽火戏诸侯', similarity: 83, tags: ['仙侠', '文青'], coverColor: coverColors[1] },
      { id: 27, title: '间客', author: '猫腻', similarity: 87, tags: ['科幻', '文青'], coverColor: coverColors[2] },
      { id: 28, title: '将夜', author: '猫腻', similarity: 90, tags: ['玄幻', '文青'], coverColor: coverColors[3] },
      { id: 29, title: '择天记', author: '猫腻', similarity: 85, tags: ['玄幻', '少年'], coverColor: coverColors[4] },
      { id: 30, title: '绍宋', author: '榴弹怕水', similarity: 74, tags: ['历史', '权谋'], coverColor: coverColors[5] }
    ]
  }
}

const currentSimilarNovels = computed(() => {
  const data = novelData[selectedNovel.value]
  return data ? data.similar : []
})

const getSimilarityColor = (val) => {
  if (val >= 90) return '#67c23a'
  if (val >= 80) return '#409eff'
  if (val >= 70) return '#e6a23c'
  return '#909399'
}

const nodeColors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#a18cd1', '#4facfe', '#fa709a']

const buildChartOption = () => {
  const data = novelData[selectedNovel.value]
  if (!data) return {}

  const centerNode = {
    name: data.center.title,
    x: 300,
    y: 300,
    symbolSize: 70,
    itemStyle: {
      color: '#667eea',
      shadowBlur: 20,
      shadowColor: 'rgba(102, 126, 234, 0.5)'
    },
    label: {
      fontSize: 14,
      fontWeight: 'bold',
      color: '#303133'
    }
  }

  const similarNodes = data.similar.map((novel, index) => {
    const angle = (Math.PI * 2 * index) / data.similar.length
    const radius = 200
    return {
      name: novel.title,
      x: 300 + radius * Math.cos(angle),
      y: 300 + radius * Math.sin(angle),
      symbolSize: 36 + novel.similarity * 0.25,
      itemStyle: {
        color: nodeColors[index % nodeColors.length],
        shadowBlur: 10,
        shadowColor: 'rgba(0, 0, 0, 0.15)'
      },
      label: {
        fontSize: 12,
        color: '#606266'
      }
    }
  })

  const links = data.similar.map((novel) => ({
    source: data.center.title,
    target: novel.title,
    value: novel.similarity,
    lineStyle: {
      width: 1 + novel.similarity / 30,
      color: novel.similarity >= 85 ? '#409eff' : '#c0c4cc',
      curveness: 0.1
    },
    label: {
      show: true,
      formatter: `${novel.similarity}%`,
      fontSize: 11,
      color: '#909399'
    }
  }))

  return {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        if (params.dataType === 'node') {
          return `<strong>${params.name}</strong>`
        }
        if (params.dataType === 'edge') {
          return `${params.data.source} → ${params.data.target}<br/>相似度: ${params.data.value}%`
        }
        return ''
      }
    },
    animationDuration: 800,
    animationEasingUpdate: 'quinticInOut',
    series: [
      {
        type: 'graph',
        layout: 'force',
        force: {
          repulsion: 600,
          gravity: 0.1,
          edgeLength: [120, 250],
          layoutAnimation: true
        },
        roam: true,
        draggable: true,
        symbol: 'circle',
        data: [centerNode, ...similarNodes],
        links: links,
        label: {
          show: true,
          position: 'bottom',
          distance: 8
        },
        edgeLabel: {
          show: true,
          fontSize: 11
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 4
          },
          itemStyle: {
            shadowBlur: 20
          }
        },
        lineStyle: {
          opacity: 0.7
        }
      }
    ]
  }
}

const initChart = () => {
  if (!chartRef.value) return
  if (chartInstance) {
    chartInstance.dispose()
  }
  chartInstance = echarts.init(chartRef.value)
  chartInstance.setOption(buildChartOption())
}

const handleResize = () => {
  chartInstance && chartInstance.resize()
}

const handleNovelChange = () => {
  nextTick(() => {
    if (chartInstance) {
      chartInstance.setOption(buildChartOption(), true)
    }
  })
}

watch(selectedNovel, () => {
  handleNovelChange()
})

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.similar-recommend-page {
  padding: $spacing-lg;
  background: $bg-page;
  min-height: calc(100vh - $top-nav-height);
}

.page-header {
  margin-bottom: $spacing-lg;

  .page-title {
    font-size: 24px;
    font-weight: 700;
    color: $text-primary;
    margin-bottom: $spacing-xs;
  }

  .page-desc {
    font-size: 14px;
    color: $text-secondary;
  }
}

.search-bar {
  margin-bottom: $spacing-lg;
  background: $bg-white;
  padding: $spacing-md $spacing-lg;
  border-radius: $border-radius-lg;
  box-shadow: $box-shadow-light;

  .novel-select {
    width: 400px;
    max-width: 100%;
  }
}

.content-layout {
  display: flex;
  gap: $spacing-lg;
  align-items: flex-start;
}

.chart-panel {
  flex: 1;
  background: $bg-white;
  border-radius: $border-radius-lg;
  box-shadow: $box-shadow-light;
  padding: $spacing-md;
  min-height: 520px;

  .relation-chart {
    width: 100%;
    height: 500px;
  }
}

.side-panel {
  width: 360px;
  flex-shrink: 0;
  background: $bg-white;
  border-radius: $border-radius-lg;
  box-shadow: $box-shadow-light;
  padding: $spacing-lg;
  max-height: 560px;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background: $border-color;
    border-radius: 2px;
  }
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: $spacing-md;
  display: flex;
  align-items: center;
  gap: $spacing-sm;

  .el-icon {
    color: $primary-color;
  }
}

.similar-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.similar-item {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-md;
  border-radius: $border-radius-md;
  background: $bg-color;
  transition: background 0.2s ease;

  &:hover {
    background: #eaecf2;
  }
}

.item-cover {
  width: 48px;
  height: 64px;
  border-radius: $border-radius-sm;
  flex-shrink: 0;
}

.item-info {
  flex: 1;
  min-width: 0;

  .item-title {
    font-size: 14px;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: 2px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .item-author {
    font-size: 12px;
    color: $text-secondary;
    margin-bottom: $spacing-xs;
  }

  .item-tags {
    display: flex;
    gap: $spacing-xs;
    flex-wrap: wrap;

    .el-tag {
      font-size: 10px;
    }
  }
}

.item-score {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;

  .score-label {
    font-size: 10px;
    color: $text-secondary;
    margin-top: 2px;
  }
}

@media (max-width: 1024px) {
  .content-layout {
    flex-direction: column;
  }

  .side-panel {
    width: 100%;
    max-height: none;
  }
}
</style>
