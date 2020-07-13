<template>
  <v-dialog v-model="showModal" persistent max-width="690">
    <v-card>
      <v-card-title class="headline">
        {{ mustaching(toDo.name) }}
      </v-card-title>
      <v-card-text>
        <ContentDisplay :content="toDo.content" />
        <CustomForm
          :id="toDo.id"
          v-model="toDo.form"
          :org="$store.state.baseInfo.org"
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn :color="$store.state.baseInfo.org.base_color" @click="$emit('close')" text>
          {{ $t('buttons.cancel') }}
        </v-btn>
        <v-btn :color="$store.state.baseInfo.org.accent_color" :loading="submittingForm" @click="submitForm" dark>
          <span v-if="toDo.form.length > 0">{{ $t('newHirePortal.submitAndComplete') }}</span><span v-else>{{ $t('newHirePortal.complete') }}</span>
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import Mustache from 'mustache'
import ContentDisplay from '../ContentDisplay'
import CustomForm from '@/components/preboarding/CustomForm'

export default {
  name: 'ToDoModal',
  components: { CustomForm, ContentDisplay },
  props: {
    toDo: {
      type: Object,
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
    },
    submitForm () {
      this.submittingForm = true
      this.$newhirepart.submitForm(this.toDo.to_do_user_id, this.toDo.form).then((data) => {
        this.toDo.completed = true
        this.$emit('close')
        if ('badges' in data && data.badges.length) {
          this.$emit('showBadge', data.badges)
        }
        if ('resources' in data && data.resources.length) {
          this.$store.dispatch('showSnackbar', this.$t('newHirePortal.addedResources'))
        }
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('newHirePortal.genericError'))
      }).finally(() => {
        this.submittingForm = false
      })
    }
  }
}
</script>
