<template>
  <v-timeline-item
    class="mb-1"
    right
  >
    <v-card color="#f5f5f5">
      <v-card-title class="title" style="padding-bottom: 0px; padding-top: 5px; max-height: 70px">
        <span style="font-size: 15px;">
          {{ $t('sideBar.unconditioned')}}
        </span>
        <div @click="selfRemove" class="red-remove" style="position: absolute; right: 15px;">
          <i style="cursor:pointer;" class="far fa-times-circle" />
        </div>
      </v-card-title>
      <v-card-text class="white text--primary pt-3">
        <CardLine :index="-1" :items="value.to_do" @openItem="openModal" @removeUnconditionedItem="removeItem" type="to_do" />
        <CardLine :index="-1" :items="value.resources" @openItem="openModal" @removeUnconditionedItem="removeItem" type="resources" />

        <v-row v-if="!value.to_do.length && !value.resources.length">
          <v-col sm="12">
            {{ $t('sequence.startByDropping') }}
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-timeline-item>
</template>

<script>
import CardLine from './CardLine'
export default {
  name: 'TimelineItem',
  components: { CardLine },
  props: {
    value: {
      type: Object,
      required: true
    }
  },
  data: () => ({
  }),
  methods: {
    openModal (item) {
      this.$emit('sendBack', item)
    },
    selfRemove () {
      this.value.to_do = []
      this.value.resources = []
      this.$store.commit('sequences/setAutoAdd')
    },
    removeItem (item) {
      const index = this.value[item.type].findIndex(a => a.id === item.id)
      this.value[item.type].splice(index, 1)
    }
  }
}
</script>

<style scoped>
</style>
