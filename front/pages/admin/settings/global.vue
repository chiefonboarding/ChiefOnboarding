<template>
  <v-container grid-list-xl fluid fill-height>
    <LoadingIcon :is-loading="loading" />
    <v-row v-if="!loading">
      <v-col sm="6">
        <GeneralPart :org="org" />
        <LanguageTemplates :org="org" />
        <ExportPart />
      </v-col>
      <v-col sm="6">
        <CustomizationPart :org="org" />
        <AdditionalSettings :org="org" />
      </v-col>
    </v-row>
  </v-container>
</template>
<script>
import GeneralPart from '@/components/admin/settings/global/GeneralPart'
import LanguageTemplates from '@/components/admin/settings/global/LanguageTemplates'
import CustomizationPart from '@/components/admin/settings/global/CustomizationPart'
import AdditionalSettings from '@/components/admin/settings/global/AdditionalSettings'
import ExportPart from '@/components/admin/settings/global/ExportPart'

export default {
  layout: 'admin',
  components: {
    AdditionalSettings,
    GeneralPart,
    LanguageTemplates,
    CustomizationPart,
    ExportPart
  },
  data: () => ({
    loading: false,
    org: {}
  }),
  mounted () {
    this.loading = true
    this.$org.getDetailOrgInfo().then((org) => {
      this.org = org
      this.loading = false
    })
  }
}
</script>
