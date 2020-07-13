<template>
  <div>
    <v-toolbar
      color="org.base_color"
      dark
      extended
      flat
    />

    <v-card
      v-if="page"
      class="mx-auto mb-4"
      max-width="590"
      style="margin-top: -64px;"
    >
      <v-card-title>
        <h2>
          {{ Mustaching(page.name) }}
        </h2>
      </v-card-title>
      <v-card-text>
        <ContentDisplay v-if="page.content !== null && page.content.length" :content="page.content" :disable-mustache="disableMustache" />
        <div v-else>
          <div v-for="j in page.content" :key="j.id">
            <blockquote class="blockquote">
              {{ j.message }}
            </blockquote>
          </div>
        </div>
        <CustomForm
          v-if="!page.completed"
          :id="page.id"
          v-model="page.form"
          :org="org"
          @input="form = arguments[0]"
        />
        <v-btn
          v-if="page.form.length > 0 && !page.completed"
          :color="org.base_color"
          :loading="sendingForm"
          @click="sendFormBack"
          style="margin-left: 0px"
          dark
        >
          {{ $t('buttons.submit') }}
        </v-btn>

        <div v-if="page.completed">
          <p>{{ $t('preboarding.completedForm') }}</p>
        </div>
        <div v-if="pages.length > 1" class="text-center mt-2">
          <v-btn :color="org.base_color" @click="clickNext" style="color: white">
            {{ $t('buttons.next') }} ->
          </v-btn>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import Mustache from 'mustache'
import ContentDisplay from '../portal/ContentDisplay'
import CustomForm from './CustomForm'

export default {
  name: 'PreboardingPage',
  components: { ContentDisplay, CustomForm },
  props: {
    pages: {
      type: Array,
      required: true
    },
    newHire: {
      type: Object,
      required: true
    },
    org: {
      type: Object,
      required: true
    },
    completedTodos: {
      type: Array,
      default: () => []
    },
    disableMustache: {
      type: Boolean,
      default: false
    }
  },
  data: () => ({
    form: [],
    dialogForm: [],
    index: 0,
    showModal: false,
    sendingForm: false,
    submittingForm: false
  }),
  computed: {
    page () {
      return this.pages[this.index]
    }
  },
  methods: {
    Mustaching (content) {
      if (this.disableMustache) { return content }
      return Mustache.render(content, this.newHire)
    },
    clickNext () {
      this.index++
      if (this.index > this.pages.length - 1) {
        this.index = 0
      }
      this.form = []
    },
    sendFormBack () {
      this.sendingForm = true
      this.$newhirepreboarding.sendFormBack({ id: this.pages[this.index].page_id, form: this.form }).then((data) => {
        this.pages[this.index].completed = true
      }).finally(() => {
        this.sendingForm = false
      })
    }
  }
}
</script>
