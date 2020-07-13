<template>
  <v-container :class="{'pa-4 grid-list-md' : !inline, 'pa-0': inline}">
    <v-row>
      <v-col cols="6" class="py-0">
        <v-col xs="12" class="py-0">
          <VTextFieldEmoji
            v-model="value.name"
            :label="$t('badge.name')"
            :errors="errorMessages.name"
            @removeError="errorMessages.name=''"
          />
        </v-col>
        <v-col xs="12" class="py-0">
          <TagsSelector v-model="value.tags" class="pt-2" />
        </v-col>
        <v-col xs="12" class="py-0">
          <Editor
            v-model="value.content"
          />
        </v-col>
        <v-col xs="12" class="py-0">
          <label> {{ $t('badge.image') }} </label>
          <v-file v-model="value.image" style="margin: 0" />
        </v-col>
      </v-col>
      <v-col cols="6" class="py-0">
        <div class="inner" style="text-align: center;">
          <img
            v-if="value.image !== null && Object.keys(value.image).length"
            :src="value.image.file_url"
            alt="image"
            style="max-width: 100%"
          >
          <div>
            {{ $t('badge.unlocked') }}
            <strong>{{ value.name }}</strong>
          </div>
          <div><ContentDisplay :content="value.content" disable-mustache /></div>
          <v-btn style="margin: 10px auto;">
            {{ $t('buttons.close') }}
          </v-btn>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import ContentDisplay from '@/components/portal/ContentDisplay'
export default {
  components: { ContentDisplay },
  props: {
    value: {
      type: Object,
      required: true
    },
    errors: {
      type: Object,
      required: true
    },
    inline: {
      default: false,
      type: Boolean
    }
  },
  computed: {
    errorMessages () {
      return JSON.parse(JSON.stringify(this.errors))
    }
  },
  watch: {
    value: {
      handler (value) {
        this.$emit('input', value)
      },
      deep: true
    },
    'value.image' (value) {
      this.value.image_id = value.id
    },
    errors (value) {
      if ('content' in value) {
        this.$store.dispatch('showSnackbar', 'Content: ' + value.content[0])
      }
    }
  }
}
</script>
