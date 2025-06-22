import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import adminUserService from '@/services/adminUserService';
import type { AdminUser, AdminUserCreatePayload, AdminUserUpdatePayload } from '@/types/adminUser';
import type { Role } from '@/types/role';
import type { PaginatedAdminUsersResponse } from '@/services/adminUserService'; // Import specific response type

export const useAdminUsersStore = defineStore('adminUsers', () => {
  // State
  const users = ref<AdminUser[]>([]);
  const selectedUser = ref<AdminUser | null>(null);
  const roles = ref<Role[]>([]);

  const isLoadingUsers = ref<boolean>(false);
  const usersError = ref<string | null>(null);

  const isLoadingRoles = ref<boolean>(false);
  const rolesError = ref<string | null>(null);

  const isLoadingSingleUser = ref<boolean>(false);
  const singleUserError = ref<string | null>(null);

  const isSubmittingUser = ref<boolean>(false); // For create/update operations
  const submitUserError = ref<string | null>(null);
  const submitUserSuccessMessage = ref<string | null>(null);

  // Pagination state for user list
  const currentPage = ref<number>(1);
  const itemsPerPage = ref<number>(10); // Default, can be updated by API response
  const totalItems = ref<number>(0);
  const totalPages = ref<number>(1);

  // Getters
  const getUserList = computed(() => users.value);
  const getSelectedUser = computed(() => selectedUser.value);
  const getRolesList = computed(() => roles.value);
  const getPaginationDetails = computed(() => ({
    currentPage: currentPage.value,
    itemsPerPage: itemsPerPage.value,
    totalItems: totalItems.value,
    totalPages: totalPages.value,
  }));

  // Actions
  async function fetchUsers(page: number = 1, limit: number = itemsPerPage.value, filters: any = {}) {
    isLoadingUsers.value = true;
    usersError.value = null;
    try {
      const response: PaginatedAdminUsersResponse = await adminUserService.fetchAdminUsers(page, limit, filters);
      users.value = response.users;
      currentPage.value = response.page;
      itemsPerPage.value = response.per_page; // Assuming backend returns per_page
      totalItems.value = response.total_items;
      totalPages.value = response.total_pages;
    } catch (err: any) {
      usersError.value = err.response?.data?.detail || err.message || 'Failed to fetch users.';
      users.value = []; // Clear on error
    } finally {
      isLoadingUsers.value = false;
    }
  }

  async function fetchUser(userId: string | number) {
    isLoadingSingleUser.value = true;
    singleUserError.value = null;
    try {
      const userData = await adminUserService.fetchAdminUserById(userId);
      selectedUser.value = userData;
      return userData; // Return for immediate use if needed
    } catch (err: any) {
      singleUserError.value = err.response?.data?.detail || err.message || `Failed to fetch user ${userId}.`;
      selectedUser.value = null;
      throw err; // Re-throw for component to handle
    } finally {
      isLoadingSingleUser.value = false;
    }
  }

  async function createUser(userData: AdminUserCreatePayload): Promise<AdminUser | null> {
    isSubmittingUser.value = true;
    submitUserError.value = null;
    submitUserSuccessMessage.value = null;
    try {
      const newUser = await adminUserService.createAdminUser(userData);
      submitUserSuccessMessage.value = `User "${newUser.username}" created successfully.`;
      // Optionally refresh user list or add to it: await fetchUsers(currentPage.value, itemsPerPage.value);
      return newUser;
    } catch (err: any) {
      submitUserError.value = err.response?.data?.detail || err.message || 'Failed to create user.';
      throw err;
    } finally {
      isSubmittingUser.value = false;
    }
  }

  async function updateUser(userId: string | number, userData: AdminUserUpdatePayload): Promise<AdminUser | null> {
    isSubmittingUser.value = true;
    submitUserError.value = null;
    submitUserSuccessMessage.value = null;
    try {
      const updatedUser = await adminUserService.updateAdminUser(userId, userData);
      selectedUser.value = updatedUser; // Update selected user if it's the one being edited
      // Update in the main list as well
      const index = users.value.findIndex(u => u.user_id === updatedUser.user_id);
      if (index !== -1) {
        users.value[index] = updatedUser;
      }
      submitUserSuccessMessage.value = `User "${updatedUser.username}" updated successfully.`;
      return updatedUser;
    } catch (err: any) {
      submitUserError.value = err.response?.data?.detail || err.message || 'Failed to update user.';
      throw err;
    } finally {
      isSubmittingUser.value = false;
    }
  }

  async function fetchRoles() {
    isLoadingRoles.value = true;
    rolesError.value = null;
    try {
      const rolesData = await adminUserService.fetchAdminRoles();
      roles.value = rolesData;
    } catch (err: any) {
      rolesError.value = err.response?.data?.detail || err.message || 'Failed to fetch roles.';
      roles.value = []; // Clear on error
    } finally {
      isLoadingRoles.value = false;
    }
  }

  function clearSubmitStatus() {
    submitUserError.value = null;
    submitUserSuccessMessage.value = null;
  }

  return {
    users, selectedUser, roles,
    isLoadingUsers, usersError,
    isLoadingRoles, rolesError,
    isLoadingSingleUser, singleUserError,
    isSubmittingUser, submitUserError, submitUserSuccessMessage,
    currentPage, itemsPerPage, totalItems, totalPages,
    getUserList, getSelectedUser, getRolesList, getPaginationDetails,
    fetchUsers, fetchUser, createUser, updateUser, fetchRoles,
    clearSubmitStatus,
  };
});
```
