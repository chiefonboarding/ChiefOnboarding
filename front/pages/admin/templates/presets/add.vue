<template>
  <TemplateCompInner>
    <template slot="header">
      <h1 class="heading" style="margin-top: 10px;">
        {{ $t('sequence.add') }}
      </h1>
    </template>
    <template slot="formpart">
      <SequenceForm ref="seq" v-model="sequence" :errors="errors" class="form" />
    </template>
    <template slot="footer">
      <v-btn :loading="saving" @click="createSequence" color="primary" style="float:right">
        {{ $t('buttons.save') }}
      </v-btn>
    </template>
  </TemplateCompInner>
</template>

<script>
import SequenceForm from '@/components/admin/sequence/Form'
export default {
  layout: 'admin',
  components: { SequenceForm },
  data: () => ({
    loading: true,
    saving: false,
    removing: false,
    duplicating: false,
    errors: {},
    sequence: {
      preboarding: [],
      to_do: [],
      resources: [],
      introductions: [],
      appointments: [],
      conditions: [],
      name: ''
    }
  }),
  mounted () {
    this.$store.commit('sequences/setSequence', [])
    this.$store.commit('sequences/setSequenceFull', this.sequence)
    this.$store.commit('sequences/resetItem')
  },
  methods: {
    createSequence () {
      this.saving = true
      this.postSeq = JSON.parse(JSON.stringify(this.sequence))
      this.postSeq.conditions = JSON.parse(JSON.stringify(this.$store.state.sequences.sequence))
      this.postSeq.collection = this.$refs.seq.collection
      this.$sequences.create(this.postSeq).then((data) => {
        this.$router.push({ name: 'admin-templates-presets' })
        this.$store.dispatch('showSnackbar', this.$t('sequence.created'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.saving = false
      })
    }
  }
}
</script>

<style scoped>
.border-bottom {
  border-bottom: 1px solid rgb(228, 228, 228);
}
</style>
