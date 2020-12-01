<template>
  <TemplateCompInner>
    <template slot="header">
      <h1 class="heading" style="margin-top: 10px;">
        {{ $t('sequence.changeHeader') }}
      </h1>
    </template>
    <template slot="header-right">
      <v-btn :loading="duplicating" @click="duplicateSequence" color="secondary">
        {{ $t('buttons.duplicate') }}
      </v-btn>
      <v-btn :loading="removing" @click="removeSequence" color="error" style="margin-right: 0px;">
        {{ $t('buttons.remove') }}
      </v-btn>
    </template>
    <template slot="formpart">
      <LoadingIcon :is-loading="loading" />
      <div v-if="!loading">
        <SequenceForm ref="seq" v-model="sequence" :errors="errors" class="form" />
      </div>
    </template>
    <template slot="footer">
      <v-btn :loading="saving" @click="updateSequence" color="primary" style="float:right">
        {{ $t('buttons.update') }}
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
    sequence: {},
    updatedSequence: {}
  }),
  watch: {
    '$route' (to, from) {
      this.getSequence()
    }
  },
  mounted () {
    this.getSequence()
  },
  methods: {
    getSequence () {
      return this.$sequences.get(this.$route.params.id).then((data) => {
        this.$store.commit('sequences/setSequence', data.conditions)
        this.$store.commit('sequences/setSequenceFull', data)
        this.sequence = data
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('sequence.noSequence'))
      }).finally(() => {
        this.loading = false
      })
    },
    updateSequence () {
      this.saving = true
      this.updatedSequence.collection = this.$refs.seq.collection
      this.updatedSequence.collection.preboarding = this.$refs.seq.preboarding
      this.updatedSequence.name = this.$store.state.sequences.item.name
      this.updatedSequence.conditions = this.$store.state.sequences.sequence
      this.$sequences.update(this.$route.params.id, this.updatedSequence).then((data) => {
        this.$router.push({ name: 'admin-templates-presets' })
        this.$store.dispatch('showSnackbar', this.$t('sequence.updated'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.saving = false
      })
    },
    removeSequence () {
      this.removing = true
      this.$sequences.remove(this.$route.params.id).then((data) => {
        this.$router.push({ name: 'admin-templates-presets' })
        this.$store.dispatch('showSnackbar', this.$t('sequence.removed'))
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.removing = false
      })
    },
    duplicateSequence () {
      this.duplicating = true
      this.sequence.collection = this.$refs.form.collection
      this.sequence.name = this.$store.state.sequences.item.name
      this.sequence.items = this.$store.state.sequences.sequence
      this.$sequences.update(this.$route.params.id, this.sequence).then((data) => {
        this.$sequences.duplicate(this.$route.params.id).then((data) => {
          this.$router.push({ name: 'admin-templates-presets' })
          this.$store.dispatch('showSnackbar', this.$t('sequence.savedAndDuplicated'))
        }).catch((error) => {
          this.errors = error
        }).finally(() => {
          this.duplicating = false
        })
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
