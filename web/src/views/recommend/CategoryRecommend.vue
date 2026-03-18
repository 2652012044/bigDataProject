<template>
  <div class="category-recommend-page">
    <div class="page-header">
      <h2 class="page-title">同类别推荐</h2>
      <p class="page-desc">根据小说类别为你推荐同类型的优质作品</p>
    </div>

    <div class="category-selector">
      <el-radio-group v-model="activeCategory" size="large" @change="handleCategoryChange">
        <el-radio-button
          v-for="cat in categoryList"
          :key="cat"
          :value="cat"
        >
          {{ cat }}
        </el-radio-button>
      </el-radio-group>
    </div>

    <el-row :gutter="20" class="novel-grid">
      <el-col
        :xs="12" :sm="8" :md="6"
        v-for="novel in currentNovels"
        :key="novel.id"
      >
        <div class="novel-card">
          <div class="card-cover" :style="{ background: novel.coverColor }">
            <div class="score-badge">{{ novel.score }}</div>
          </div>
          <div class="card-body">
            <div class="card-title" :title="novel.title">{{ novel.title }}</div>
            <div class="card-author">{{ novel.author }}</div>
            <div class="card-reason">
              <el-icon><Connection /></el-icon>
              {{ novel.reason }}
            </div>
            <div class="card-tags">
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
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Connection } from '@element-plus/icons-vue'

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

const categoryList = ['玄幻', '都市', '仙侠', '科幻', '言情']
const activeCategory = ref('玄幻')

const allNovels = {
  '玄幻': [
    { id: 1, title: '斗破苍穹', author: '天蚕土豆', score: 9.6, reason: '与《武动乾坤》相似度92%', tags: ['热血', '升级'] },
    { id: 2, title: '完美世界', author: '辰东', score: 9.4, reason: '与《遮天》相似度95%', tags: ['远古', '荒'] },
    { id: 3, title: '大主宰', author: '天蚕土豆', score: 9.1, reason: '与《斗破苍穹》相似度88%', tags: ['热血', '少年'] },
    { id: 4, title: '武动乾坤', author: '天蚕土豆', score: 9.0, reason: '与《斗破苍穹》相似度90%', tags: ['修炼', '争霸'] },
    { id: 5, title: '帝霸', author: '厌笔萧生', score: 8.8, reason: '与《遮天》相似度82%', tags: ['无敌', '装逼'] },
    { id: 6, title: '万古神帝', author: '飞天鱼', score: 8.7, reason: '与《完美世界》相似度78%', tags: ['重生', '热血'] },
    { id: 7, title: '伏天氏', author: '净无痕', score: 8.9, reason: '与《大主宰》相似度85%', tags: ['天才', '崛起'] },
    { id: 8, title: '万相之王', author: '天蚕土豆', score: 8.7, reason: '与《斗破苍穹》相似度86%', tags: ['双主角', '升级'] }
  ],
  '都市': [
    { id: 9, title: '全职法师', author: '乱', score: 9.2, reason: '与《最强弃少》相似度80%', tags: ['都市', '法师'] },
    { id: 10, title: '我的26岁女房客', author: '独悟', score: 8.5, reason: '与《校花的贴身高手》相似度75%', tags: ['都市', '暧昧'] },
    { id: 11, title: '天才医生', author: '柳下挥', score: 8.8, reason: '与《超级医生》相似度88%', tags: ['医术', '都市'] },
    { id: 12, title: '超级神基因', author: '十二翼黑暗炽天使', score: 9.0, reason: '与《全职法师》相似度83%', tags: ['进化', '冒险'] },
    { id: 13, title: '夜的命名术', author: '会说话的肘子', score: 8.9, reason: '与《大王饶命》相似度91%', tags: ['幽默', '冒险'] },
    { id: 14, title: '大王饶命', author: '会说话的肘子', score: 9.3, reason: '与《夜的命名术》相似度91%', tags: ['搞笑', '升级'] },
    { id: 15, title: '我有一座恐怖屋', author: '我会修空调', score: 9.1, reason: '与《深夜书屋》相似度79%', tags: ['灵异', '冒险'] },
    { id: 16, title: '全球高武', author: '老鹰吃小鸡', score: 8.8, reason: '与《全职法师》相似度76%', tags: ['武道', '都市'] }
  ],
  '仙侠': [
    { id: 17, title: '凡人修仙传', author: '忘语', score: 9.5, reason: '与《一世之尊》相似度85%', tags: ['修仙', '凡人流'] },
    { id: 18, title: '剑来', author: '烽火戏诸侯', score: 9.5, reason: '与《雪中悍刀行》相似度89%', tags: ['剑道', '文青'] },
    { id: 19, title: '大奉打更人', author: '卖报小郎君', score: 9.3, reason: '与《牧神记》相似度80%', tags: ['探案', '修仙'] },
    { id: 20, title: '道诡异仙', author: '狐尾的笔', score: 9.1, reason: '与《诡秘之主》相似度87%', tags: ['诡异', '修仙'] },
    { id: 21, title: '一世之尊', author: '爱潜水的乌贼', score: 9.4, reason: '与《凡人修仙传》相似度85%', tags: ['多主角', '修仙'] },
    { id: 22, title: '赤心巡天', author: '情何以甚', score: 9.1, reason: '与《剑来》相似度82%', tags: ['修仙', '热血'] },
    { id: 23, title: '牧神记', author: '宅猪', score: 9.3, reason: '与《大奉打更人》相似度80%', tags: ['少年', '成长'] },
    { id: 24, title: '我师兄实在太稳健了', author: '言归正传', score: 9.0, reason: '与《凡人修仙传》相似度78%', tags: ['稳健', '搞笑'] }
  ],
  '科幻': [
    { id: 25, title: '超神机械师', author: '齐佩甲', score: 9.0, reason: '与《深空彼岸》相似度81%', tags: ['星际', '机械'] },
    { id: 26, title: '深空彼岸', author: '辰东', score: 8.8, reason: '与《超神机械师》相似度81%', tags: ['科幻', '进化'] },
    { id: 27, title: '吞噬星空', author: '我吃西红柿', score: 9.2, reason: '与《超神机械师》相似度86%', tags: ['星际', '武者'] },
    { id: 28, title: '小兵传奇', author: '玄雨', score: 8.5, reason: '与《吞噬星空》相似度74%', tags: ['军事', '星际'] },
    { id: 29, title: '星门', author: '辰东', score: 8.6, reason: '与《深空彼岸》相似度92%', tags: ['末世', '进化'] },
    { id: 30, title: '学霸的黑科技系统', author: '晨星LL', score: 8.9, reason: '与《天才医生》相似度70%', tags: ['学术', '系统'] },
    { id: 31, title: '长夜余火', author: '爱潜水的乌贼', score: 8.9, reason: '与《深空彼岸》相似度77%', tags: ['末世', '冒险'] },
    { id: 32, title: '地球纪元', author: '彩虹之门', score: 8.7, reason: '与《吞噬星空》相似度72%', tags: ['硬科幻', '末世'] }
  ],
  '言情': [
    { id: 33, title: '微微一笑很倾城', author: '顾漫', score: 9.1, reason: '与《何以笙箫默》相似度90%', tags: ['甜宠', '游戏'] },
    { id: 34, title: '何以笙箫默', author: '顾漫', score: 9.3, reason: '与《微微一笑很倾城》相似度90%', tags: ['都市', '虐恋'] },
    { id: 35, title: '你好，旧时光', author: '八月长安', score: 9.0, reason: '与《最好的我们》相似度93%', tags: ['青春', '校园'] },
    { id: 36, title: '最好的我们', author: '八月长安', score: 9.2, reason: '与《你好，旧时光》相似度93%', tags: ['青春', '成长'] },
    { id: 37, title: '知否知否应是绿肥红瘦', author: '关心则乱', score: 9.1, reason: '与《庶女明兰传》相似度88%', tags: ['古代', '宅斗'] },
    { id: 38, title: '三生三世十里桃花', author: '唐七', score: 8.8, reason: '与《花千骨》相似度82%', tags: ['仙侠', '虐恋'] },
    { id: 39, title: '香蜜沉沉烬如霜', author: '电线', score: 8.9, reason: '与《三生三世》相似度85%', tags: ['仙侠', '甜虐'] },
    { id: 40, title: '致我们终将逝去的青春', author: '辛夷坞', score: 8.7, reason: '与《最好的我们》相似度80%', tags: ['青春', '怀旧'] }
  ]
}

const currentNovels = computed(() => {
  const novels = allNovels[activeCategory.value] || []
  return novels.map((novel, index) => ({
    ...novel,
    coverColor: coverColors[index % coverColors.length]
  }))
})

const handleCategoryChange = () => {
  // Data reactively updates via computed property
}
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.category-recommend-page {
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

.category-selector {
  margin-bottom: $spacing-lg;
  background: $bg-white;
  padding: $spacing-md $spacing-lg;
  border-radius: $border-radius-lg;
  box-shadow: $box-shadow-light;

  :deep(.el-radio-button__inner) {
    border-radius: $border-radius-md !important;
    border: none;
    padding: 10px 28px;
    font-weight: 500;
  }

  :deep(.el-radio-group) {
    flex-wrap: wrap;
    gap: $spacing-sm;
  }
}

.novel-grid {
  .el-col {
    margin-bottom: 20px;
  }
}

.novel-card {
  background: $bg-white;
  border-radius: $border-radius-lg;
  overflow: hidden;
  box-shadow: $box-shadow-light;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  cursor: pointer;
  height: 100%;

  &:hover {
    transform: translateY(-6px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.12);
  }
}

.card-cover {
  height: 180px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;

  .score-badge {
    position: absolute;
    top: $spacing-sm;
    right: $spacing-sm;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(8px);
    color: #fff;
    font-size: 14px;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 16px;
  }
}

.card-body {
  padding: $spacing-md;

  .card-title {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin-bottom: $spacing-xs;
  }

  .card-author {
    font-size: 13px;
    color: $text-secondary;
    margin-bottom: $spacing-sm;
  }

  .card-reason {
    font-size: 12px;
    color: $primary-color;
    background: rgba(64, 158, 255, 0.08);
    padding: $spacing-xs $spacing-sm;
    border-radius: $border-radius-sm;
    margin-bottom: $spacing-sm;
    display: flex;
    align-items: center;
    gap: 4px;
    line-height: 1.4;

    .el-icon {
      flex-shrink: 0;
    }
  }

  .card-tags {
    display: flex;
    flex-wrap: wrap;
    gap: $spacing-xs;

    .el-tag {
      font-size: 11px;
    }
  }
}
</style>
