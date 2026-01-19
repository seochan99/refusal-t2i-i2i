// Analytics utilities for tracking user behavior
import { logEvent, setUserProperties } from "firebase/analytics";
import { analytics } from "./firebase";

export function trackPageView(page: string, params?: Record<string, any>) {
  if (analytics && typeof window !== 'undefined') {
    try {
      logEvent(analytics, 'page_view', {
        page_title: page,
        page_location: window.location.href,
        ...params
      });
    } catch (error) {
      console.warn('Analytics page view tracking failed:', error);
    }
  }
}

export function trackEvent(event: string, params?: Record<string, any>) {
  if (analytics && typeof window !== 'undefined') {
    try {
      logEvent(analytics, event, params);
    } catch (error) {
      console.warn('Analytics event tracking failed:', error);
    }
  }
}

export function trackEvaluationStart(experiment: string, model: string) {
  trackEvent('evaluation_start', {
    experiment_type: experiment,
    model_name: model,
    timestamp: Date.now()
  });
}

export function trackEvaluationComplete(experiment: string, model: string, duration: number, itemCount: number) {
  trackEvent('evaluation_complete', {
    experiment_type: experiment,
    model_name: model,
    duration_ms: duration,
    items_evaluated: itemCount,
    timestamp: Date.now()
  });
}

export function trackTaskStart(taskId: number) {
  trackEvent('task_start', {
    task_id: taskId,
    timestamp: Date.now()
  });
}

export function trackTaskComplete(taskId: number, duration: number, itemCount: number) {
  trackEvent('task_complete', {
    task_id: taskId,
    duration_ms: duration,
    items_evaluated: itemCount,
    timestamp: Date.now()
  });
}

export function setUserType(userType: 'regular' | 'prolific' | 'amt') {
  if (analytics && typeof window !== 'undefined') {
    try {
      setUserProperties(analytics, {
        user_type: userType
      });
    } catch (error) {
      console.warn('Analytics user properties failed:', error);
    }
  }
}

export function trackError(errorType: string, errorMessage: string, context?: Record<string, any>) {
  trackEvent('error_occurred', {
    error_type: errorType,
    error_message: errorMessage,
    ...context
  });
}

export function trackButtonClick(buttonName: string, context?: Record<string, any>) {
  trackEvent('button_click', {
    button_name: buttonName,
    ...context
  });
}

export function trackSessionStart(sessionType: string) {
  trackEvent('session_start', {
    session_type: sessionType,
    timestamp: Date.now()
  });
}

export function trackSessionEnd(sessionType: string, duration: number) {
  trackEvent('session_end', {
    session_type: sessionType,
    duration_ms: duration,
    timestamp: Date.now()
  });
}