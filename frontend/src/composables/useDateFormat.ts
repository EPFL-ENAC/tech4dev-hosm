import { useI18n } from 'vue-i18n';

/**
 * Composable for formatting dates with locale support.
 * Returns a function to format ISO date strings to localized strings.
 */
export function useDateFormat() {
  const { locale } = useI18n();

  /**
   * Format an ISO date string to a localized date/time string.
   * @param dateString - ISO date string (e.g., "2024-01-15T10:30:00Z")
   * @returns Formatted date string or empty string if invalid
   */
  function formatDate(dateString: string): string {
    if (!dateString) return '';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '';

    if (locale.value === 'fr') {
      return date.toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    }

    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  return {
    formatDate,
  };
}
