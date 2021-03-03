<template>
  <v-row>
    <v-col sm="12" mb="6" offset-mb="3" md="6" offset-sm="3">
      <v-row class="mb-4">
        <v-col sm="6">
          <h1 class="heading" style="margin-top: 5px;">
            {{ $t('settings.admin') }}
          </h1>
        </v-col>
        <v-col sm="6" class="text-right">
          <AdminAddDialog />
        </v-col>
      </v-row>
      <v-card class="mb-4">
        <template>
          <v-data-table
            :headers="[{text: 'Name', value: 'full_name'}, { value: 'email'}]"
            :items="$store.state.admins"
            :loading="loading"
            :footer-props="{'items-per-page-options':[50, 100, -1]}"
            class="elevation-1"
          >
            <template v-slot:item.full_name="{ item }">
              {{ item.full_name }} (<span v-if="item.role === 1">{{ $t('settings.fullAccess') }}</span><span v-else>{{ $t('settings.limitedAccess') }}</span>)
            </template>
            <template v-slot:item.email="{ item }">
              <AdminDialog :id="item.id" v-if="$store.state.admin.id !== item.id" />
            </template>
            <template v-slot:no-data>
              {{ $t('settings.onlyYou') }}
            </template>
          </v-data-table>
        </template>
      </v-card>
    </v-col>
  </v-row>
</template>
<script>
import AdminDialog from '@/components/admin/settings/AdministratorDialog'
import AdminAddDialog from '@/components/admin/settings/AdministratorAddDialog'
export default {
  layout: 'admin',
  components: { AdminDialog, AdminAddDialog },
  data () {
    return {
      dialog: false,
      loading: false
    }
  },
  mounted () {
    this.loading = true
    this.$org.getAdmins().then((admins) => {
      this.loading = false
    })
  }
}
</script>
