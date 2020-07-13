<template>
  <v-dialog v-model="showModal" persistent max-width="690">
    <v-card class="text-center">
      <v-card-title class="headline">
        {{ mustaching(badge.name) }}
      </v-card-title>
      <v-card-text>
        <div v-for="i in badge">
          <v-row v-if="i.image !== '' && i.image !== null" class="text-center">
            <v-img :max-height="200" :max-width="200" :src="i.image" class="text-center" />
          </v-row>
          <ContentDisplay :content="i.content" />
        </div>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn :color="$store.state.baseInfo.org.base_color" @click="$emit('close')" text>
          {{ $t('buttons.close') }}
        </v-btn>
        <v-spacer />
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import Mustache from 'mustache'
import ContentDisplay from '../ContentDisplay'

export default {
  name: 'ToDoModal',
  components: { ContentDisplay },
  props: {
    badge: {
      type: Array,
      required: true
    },
    showModal: {
      type: Boolean,
      required: true
    }
  },
  data: () => ({
    submittingForm: false
  }),
  methods: {
    mustaching (content) {
      if (content === undefined) { return '' }
      return Mustache.render(content, this.$store.state.baseInfo)
    }
  }
}
</script>
