<template>
  <div class="hot-recommend-page">
    <div class="page-header">
      <h2 class="page-title">热门推荐</h2>
      <p class="page-desc">根据全站用户阅读数据，为你精选最受欢迎的小说</p>
    </div>

    <div class="category-row" v-for="category in categories" :key="category.name">
      <div class="row-header">
        <h3 class="row-title">
          <el-icon><Pointer /></el-icon>
          {{ category.name }}
        </h3>
        <el-button text type="primary" class="view-all-btn">
          查看全部
          <el-icon class="el-icon--right"><ArrowRight /></el-icon>
        </el-button>
      </div>
      <div class="scroll-container">
        <div class="scroll-track">
          <div
            class="novel-card"
            v-for="novel in category.novels"
            :key="novel.id"
          >
            <div class="cover-area" :style="{ background: novel.coverColor }">
              <div class="cover-gradient">
                <span class="cover-score">{{ novel.score }}</span>
                <div class="cover-info">
                  <span class="cover-title">{{ novel.title }}</span>
                  <span class="cover-author">{{ novel.author }}</span>
                </div>
              </div>
            </div>
            <div class="card-meta">
              <div class="meta-title" :title="novel.title">{{ novel.title }}</div>
              <div class="meta-bottom">
                <span class="meta-author">{{ novel.author }}</span>
                <el-tag size="small" type="warning" effect="plain">{{ novel.tag }}</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { Pointer, ArrowRight } from '@element-plus/icons-vue'

const coverColors = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
  'linear-gradient(135deg, #fccb90 0%, #d57eeb 100%)',
  'linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)'
]

const generateNovels = (list) => {
  return list.map((item, index) => ({
    id: item.id,
    title: item.title,
    author: item.author,
    score: item.score,
    tag: item.tag,
    coverColor: coverColors[index % coverColors.length]
  }))
}

const categories = reactive([
  {
    name: '本周最热',
    novels: generateNovels([
      { id: 1, title: '斗破苍穹', author: '天蚕土豆', score: 9.6, tag: '玄幻' },
      { id: 2, title: '完美世界', author: '辰东', score: 9.4, tag: '玄幻' },
      { id: 3, title: '凡人修仙传', author: '忘语', score: 9.5, tag: '仙侠' },
      { id: 4, title: '诡秘之主', author: '爱潜水的乌贼', score: 9.7, tag: '奇幻' },
      { id: 5, title: '大奉打更人', author: '卖报小郎君', score: 9.3, tag: '仙侠' },
      { id: 6, title: '神印王座', author: '唐家三少', score: 8.9, tag: '玄幻' },
      { id: 7, title: '雪中悍刀行', author: '烽火戏诸侯', score: 9.2, tag: '武侠' },
      { id: 8, title: '庆余年', author: '猫腻', score: 9.5, tag: '架空' }
    ])
  },
  {
    name: '新书速递',
    novels: generateNovels([
      { id: 9, title: '道诡异仙', author: '狐尾的笔', score: 9.1, tag: '仙侠' },
      { id: 10, title: '深空彼岸', author: '辰东', score: 8.8, tag: '科幻' },
      { id: 11, title: '宿命之环', author: '爱潜水的乌贼', score: 9.3, tag: '奇幻' },
      { id: 12, title: '万相之王', author: '天蚕土豆', score: 8.7, tag: '玄幻' },
      { id: 13, title: '长夜余火', author: '爱潜水的乌贼', score: 8.9, tag: '科幻' },
      { id: 14, title: '星门', author: '辰东', score: 8.6, tag: '科幻' },
      { id: 15, title: '我师兄实在太稳健了', author: '言归正传', score: 9.0, tag: '仙侠' },
      { id: 16, title: '烂柯棋缘', author: '真费事', score: 8.8, tag: '仙侠' }
    ])
  },
  {
    name: '口碑佳作',
    novels: generateNovels([
      { id: 17, title: '遮天', author: '辰东', score: 9.6, tag: '玄幻' },
      { id: 18, title: '一世之尊', author: '爱潜水的乌贼', score: 9.4, tag: '仙侠' },
      { id: 19, title: '牧神记', author: '宅猪', score: 9.3, tag: '玄幻' },
      { id: 20, title: '剑来', author: '烽火戏诸侯', score: 9.5, tag: '仙侠' },
      { id: 21, title: '绍宋', author: '榴弹怕水', score: 9.2, tag: '历史' },
      { id: 22, title: '超神机械师', author: '齐佩甲', score: 9.0, tag: '科幻' },
      { id: 23, title: '赤心巡天', author: '情何以甚', score: 9.1, tag: '仙侠' },
      { id: 24, title: '夜的命名术', author: '会说话的肘子', score: 8.9, tag: '都市' }
    ])
  }
])
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.hot-recommend-page {
  padding: $spacing-lg;
  background: $bg-page;
  min-height: calc(100vh - $top-nav-height);
}

.page-header {
  margin-bottom: $spacing-xl;

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

.category-row {
  margin-bottom: $spacing-xl;
  background: $bg-white;
  border-radius: $border-radius-lg;
  padding: $spacing-lg;
  box-shadow: $box-shadow-light;
}

.row-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-md;

  .row-title {
    font-size: 18px;
    font-weight: 600;
    color: $text-primary;
    display: flex;
    align-items: center;
    gap: $spacing-sm;

    .el-icon {
      color: $warning-color;
    }
  }

  .view-all-btn {
    font-size: 14px;
  }
}

.scroll-container {
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: $spacing-sm;

  &::-webkit-scrollbar {
    height: 6px;
  }

  &::-webkit-scrollbar-track {
    background: $bg-color;
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb {
    background: $border-color;
    border-radius: 3px;

    &:hover {
      background: $text-secondary;
    }
  }
}

.scroll-track {
  display: flex;
  gap: $spacing-md;
  padding: $spacing-xs;
}

.novel-card {
  flex: 0 0 180px;
  width: 180px;
  border-radius: $border-radius-md;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  background: $bg-white;
  box-shadow: $box-shadow-light;

  &:hover {
    transform: translateY(-6px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
  }
}

.cover-area {
  width: 100%;
  height: 240px;
  position: relative;
  overflow: hidden;
}

.cover-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to top,
    rgba(0, 0, 0, 0.85) 0%,
    rgba(0, 0, 0, 0.2) 50%,
    transparent 100%
  );
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: $spacing-md;
}

.cover-score {
  align-self: flex-end;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(8px);
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 700;
  color: #fff;
}

.cover-info {
  display: flex;
  flex-direction: column;
  gap: 4px;

  .cover-title {
    font-size: 15px;
    font-weight: 600;
    color: #fff;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .cover-author {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.75);
  }
}

.card-meta {
  padding: $spacing-sm $spacing-md;

  .meta-title {
    font-size: 14px;
    font-weight: 600;
    color: $text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin-bottom: $spacing-xs;
  }

  .meta-bottom {
    display: flex;
    align-items: center;
    justify-content: space-between;

    .meta-author {
      font-size: 12px;
      color: $text-secondary;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      max-width: 90px;
    }
  }
}
</style>
