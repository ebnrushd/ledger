<template>
  <div class="user-form-view p-4 md:p-6 lg:p-8">
    <div class="max-w-2xl mx-auto">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl md:text-3xl font-semibold text-gray-800">
          {{ pageTitle }}
          <span v-if="isEditMode && userBeingEdited" class="text-gray-600">- {{ userBeingEdited.username }}</span>
        </h1>
        <router-link :to="{ name: 'AdminUserList' }"
                     class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition">
          &larr; Back to User List
        </router-link>
      </div>

      <div class="bg-white p-6 md:p-8 rounded-xl shadow-2xl">
        <div v-if="usersStore.isLoadingSingleUser && isEditMode" class="text-center py-10">
          <div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-admin-primary mx-auto"></div>
          <p class="mt-3 text-gray-600">Loading user data...</p>
        </div>
        <div v-if="usersStore.singleUserError && isEditMode"
             class="bg-red-50 border-l-4 border-red-400 text-red-700 p-4 mb-6 rounded-md shadow-md" role="alert">
          <p class="font-bold">Error Loading User</p>
          <p>{{ usersStore.singleUserError }}</p>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-6"
              v-if="!usersStore.isLoadingSingleUser || !isEditMode">

          <div v-if="usersStore.submitUserError"
               class="p-3 bg-red-100 text-red-700 border border-red-400 rounded-md text-sm">
            <p class="font-bold">Could not save user:</p>
            <p>{{ usersStore.submitUserError }}</p>
          </div>
           <div v-if="clientFormError"
               class="p-3 bg-red-100 text-red-700 border border-red-400 rounded-md text-sm">
            {{ clientFormError }}
          </div>


          <div>
            <label for="username" class="block text-sm font-medium text-gray-700">Username (Login Email) <span class="text-red-500">*</span></label>
            <input type="email" id="username" v-model="formData.username" required
                   :disabled="isEditMode"
                   class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm disabled:bg-gray-100 disabled:text-gray-500">
             <small v-if="isEditMode" class="text-xs text-gray-500">Username cannot be changed after creation.</small>
          </div>

          <div>
            <label for="email" class="block text-sm font-medium text-gray-700">Contact Email <span class="text-red-500">*</span></label>
            <input type="email" id="email" v-model="formData.email" required
                   class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm">
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-gray-700">Password <span v-if="!isEditMode" class="text-red-500">*</span></label>
            <input type="password" id="password" v-model="formData.password" :placeholder="isEditMode ? 'Leave blank to keep current password' : ''" :required="!isEditMode"
                   class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm">
          </div>

          <div>
            <label for="role_id" class="block text-sm font-medium text-gray-700">Role <span class="text-red-500">*</span></label>
            <select id="role_id" v-model="formData.role_id" required
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm bg-white">
              <option value="" disabled>Select a role</option>
              <option v-for="role in usersStore.roles" :key="role.role_id" :value="role.role_id">
                {{ role.role_name.charAt(0).toUpperCase() + role.role_name.slice(1) }}
              </option>
            </select>
            <div v-if="usersStore.isLoadingRoles" class="text-xs text-gray-500 mt-1">Loading roles...</div>
            <div v-if="usersStore.rolesError" class="text-xs text-red-500 mt-1">Could not load roles: {{ usersStore.rolesError }}</div>
          </div>

          <div>
            <label for="customer_id" class="block text-sm font-medium text-gray-700">Link to Customer ID (Optional)</label>
            <input type="number" id="customer_id" v-model.number="formData.customer_id"
                   class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-admin-primary focus:border-admin-primary sm:text-sm" placeholder="Enter Customer ID (if applicable)">
          </div>

          <div class="flex items-center">
            <input type="checkbox" id="is_active" v-model="formData.is_active"
                   class="h-4 w-4 text-admin-primary border-gray-300 rounded focus:ring-admin-primary">
            <label for="is_active" class="ml-2 block text-sm text-gray-900">User is Active</label>
          </div>

          <div class="flex justify-end space-x-4 pt-4 border-t mt-6">
            <router-link :to="{ name: 'AdminUserList' }"
                         class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-admin-primary">
              Cancel
            </router-link>
            <button type="submit"
                    class="px-6 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-admin-primary hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-admin-primary disabled:opacity-50 disabled:cursor-not-allowed"
                    :disabled="usersStore.isSubmittingUser">
              {{ usersStore.isSubmittingUser ? (isEditMode ? 'Updating...' : 'Creating...') : (isEditMode ? 'Save Changes' : 'Create User') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed, watch, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAdminUsersStore } from '@/store/adminUsers';
import type { AdminUserCreatePayload, AdminUserUpdatePayload, UserSchema } from '@/models';

export default defineComponent({
  name: 'UserFormView',
  props: {
    userId: {
      type: String,
      required: false,
    },
  },
  setup(props) {
    const usersStore = useAdminUsersStore();
    const router = useRouter();
    const route = useRoute(); // To access query params like success_message

    const isEditMode = computed(() => !!props.userId);
    const pageTitle = computed(() => isEditMode.value ? 'Edit User' : 'Create New User');
    const userBeingEdited = computed(() => usersStore.selectedUser); // For displaying username in title

    const formData = ref({
      username: '', // Will be email used for login
      email: '',    // Contact email
      password: '',
      role_id: '' as string | number, // Allow empty for initial select state
      customer_id: null as number | null | undefined, // Allow undefined for Pydantic optional
      is_active: true,
    });
    const clientFormError = ref<string | null>(null);

    const populateForm = (userData: UserSchema | AdminUserCreatePayload) => {
        formData.value.username = userData.username;
        formData.value.email = userData.email;
        formData.value.role_id = (userData as any).role_id; // Assuming role_id is present
        formData.value.customer_id = (userData as any).customer_id === undefined ? null : (userData as any).customer_id;
        formData.value.is_active = (userData as any).is_active === undefined ? true : (userData as any).is_active;
        formData.value.password = ''; // Clear password for edit form
    };

    onMounted(async () => {
      usersStore.clearSubmitStatus(); // Clear any previous submit errors/success
      await usersStore.fetchRoles(); // Fetch roles for the dropdown

      if (isEditMode.value && props.userId) {
        try {
          // Fetch the specific user for editing
          const fetchedUser = await usersStore.fetchUser(props.userId); // This sets selectedUser
          if (fetchedUser) { // selectedUser might be reactive, or use returned value
            populateForm(fetchedUser);
          } else {
             clientFormError.value = "User data not found."; // Should be caught by store error too
          }
        } catch (e) {
            // Error already set in store by fetchUser, or handle here
            console.error("Error fetching user for edit:", e);
        }
      } else {
        // Create mode: set defaults
        formData.value = {
            username: '', email: '', password: '', role_id: '',
            customer_id: null, is_active: true
        };
      }
    });

    // Watch for changes in selectedUser if it's fetched asynchronously and form needs repopulation
     watch(() => usersStore.selectedUser, (newUser) => {
        if (isEditMode.value && newUser && newUser.user_id === Number(props.userId)) {
            populateForm(newUser);
        }
     }, { deep: true });


    const handleSubmit = async () => {
      clientFormError.value = null;
      usersStore.clearSubmitStatus();

      if (!formData.value.role_id) {
        clientFormError.value = "Please select a role for the user.";
        return;
      }
      if (!isEditMode.value && (!formData.value.password || formData.value.password.length < 8)) {
        clientFormError.value = "Password must be at least 8 characters for new users.";
        return;
      }
       if (isEditMode.value && formData.value.password && formData.value.password.length < 8) {
        clientFormError.value = "New password must be at least 8 characters if provided.";
        return;
      }

      const payload: AdminUserCreatePayload | AdminUserUpdatePayload = {
        username: formData.value.username,
        email: formData.value.email,
        role_id: Number(formData.value.role_id),
        customer_id: formData.value.customer_id ? Number(formData.value.customer_id) : undefined,
        is_active: formData.value.is_active,
      };
      if (formData.value.password) { // Only include password if provided (especially for update)
        (payload as any).password = formData.value.password;
      }
      if (!isEditMode.value && !formData.value.password) { // Password required for create
         clientFormError.value = "Password is required for new users.";
         return;
      }


      let success = false;
      try {
        if (isEditMode.value && props.userId) {
          await usersStore.updateUser(props.userId, payload as AdminUserUpdatePayload);
        } else {
          await usersStore.createUser(payload as AdminUserCreatePayload);
        }
        success = !usersStore.submitUserError; // Check if store action had an error
      } catch (e) {
        // Error already set in store by action, component can just react
        console.error("Form submission error caught in component:", e);
      }

      if (success) {
        router.push({
            name: 'AdminUserList',
            query: { success_message: `User ${isEditMode.value ? 'updated' : 'created'} successfully.` }
        });
      }
      // If error, template will display usersStore.submitUserError
    };

    onUnmounted(() => {
        usersStore.clearSubmitStatus();
        usersStore.selectedUser = null; // Clear selected user when leaving form
    });

    return {
      isEditMode, pageTitle, userBeingEdited,
      formData, availableRoles: computed(() => usersStore.roles), // Make roles computed for reactivity
      isLoading: computed(() => usersStore.isLoadingSingleUser && isEditMode.value), // Loading for initial fetch
      error: computed(() => usersStore.singleUserError), // Error for initial fetch
      isSubmitting: computed(() => usersStore.isSubmittingUser),
      clientFormError, // For client-side form validation errors
      usersStore, // Provide store to template for submitError/SuccessMessage
      handleSubmit,
    };
  },
});
</script>

<style scoped>
/* Using Tailwind classes directly. Add specific overrides if necessary. */
.btn-admin-primary, .btn-admin-secondary-outline {
  @apply py-2 px-4 font-semibold rounded-lg shadow-md focus:outline-none focus:ring-2 focus:ring-opacity-75 disabled:opacity-50;
}
.btn-admin-primary { @apply bg-admin-primary text-white hover:bg-blue-700 focus:ring-blue-500; }
.btn-admin-secondary-outline { @apply bg-white text-gray-600 border border-gray-300 hover:bg-gray-50 focus:ring-admin-primary; }
</style>
```
