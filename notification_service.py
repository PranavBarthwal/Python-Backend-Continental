import logging
from datetime import datetime, timedelta
from app import db
from models import Notification, User, MedicineTracker

logger = logging.getLogger(__name__)

def create_notification(user_id, title, message, notification_type, scheduled_for=None, extra_data=None):
    """
    Create a new notification for a user
    """
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            scheduled_for=scheduled_for or datetime.utcnow(),
            extra_data=extra_data or {}
        )
        
        db.session.add(notification)
        db.session.commit()
        
        logger.info(f"Notification created for user {user_id}: {title}")
        return notification.id
        
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        db.session.rollback()
        return None

def get_user_notifications(user_id, limit=50, include_read=True):
    """
    Get notifications for a user
    """
    try:
        query = Notification.query.filter_by(user_id=user_id)
        
        if not include_read:
            query = query.filter_by(is_read=False)
        
        notifications = query.order_by(
            Notification.created_at.desc()
        ).limit(limit).all()
        
        notifications_list = []
        for notification in notifications:
            notifications_list.append({
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "notification_type": notification.notification_type,
                "is_read": notification.is_read,
                "scheduled_for": notification.scheduled_for.isoformat() if notification.scheduled_for else None,
                "created_at": notification.created_at.isoformat(),
                "extra_data": notification.extra_data
            })
        
        return notifications_list
        
    except Exception as e:
        logger.error(f"Error getting notifications for user {user_id}: {str(e)}")
        return []

def mark_notification_as_read(notification_id, user_id):
    """
    Mark a notification as read
    """
    try:
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()
        
        if notification:
            notification.is_read = True
            db.session.commit()
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        db.session.rollback()
        return False

def send_medicine_reminders():
    """
    Send medicine reminder notifications
    This function should be called by a scheduled job
    """
    try:
        from datetime import time
        current_time = datetime.now().time()
        current_date = datetime.now().date()
        
        # Get all active medicine trackers
        trackers = MedicineTracker.query.filter_by(is_active=True).all()
        
        for tracker in trackers:
            # Check if it's time for a reminder
            for timing in tracker.timing:
                reminder_time = datetime.strptime(timing.get('time', '08:00'), '%H:%M').time()
                
                # Check if current time matches reminder time (within 5 minutes)
                time_diff = abs(
                    (datetime.combine(current_date, current_time) - 
                     datetime.combine(current_date, reminder_time)).total_seconds()
                )
                
                if time_diff <= 300:  # 5 minutes tolerance
                    # Check if reminder already sent today
                    today_notifications = Notification.query.filter(
                        Notification.user_id == tracker.user_id,
                        Notification.notification_type == 'medicine_reminder',
                        Notification.created_at >= datetime.combine(current_date, time.min),
                        Notification.extra_data['medicine_tracker_id'].astext == tracker.id
                    ).count()
                    
                    if today_notifications == 0:
                        create_notification(
                            tracker.user_id,
                            "Medicine Reminder",
                            f"Time to take {tracker.medicine_name} - {tracker.dosage}",
                            "medicine_reminder",
                            extra_data={
                                "medicine_tracker_id": tracker.id,
                                "timing": timing
                            }
                        )
        
        logger.info("Medicine reminders sent successfully")
        
    except Exception as e:
        logger.error(f"Error sending medicine reminders: {str(e)}")

def send_appointment_reminders():
    """
    Send appointment reminder notifications
    This function should be called by a scheduled job
    """
    try:
        from models import Appointment
        
        # Get appointments for tomorrow
        tomorrow = datetime.now().date() + timedelta(days=1)
        appointments = Appointment.query.filter(
            Appointment.appointment_date == tomorrow,
            Appointment.status == 'scheduled'
        ).all()
        
        for appointment in appointments:
            # Check if reminder already sent
            existing_reminder = Notification.query.filter(
                Notification.user_id == appointment.user_id,
                Notification.notification_type == 'appointment_reminder',
                Notification.extra_data['appointment_id'].astext == appointment.id
            ).first()
            
            if not existing_reminder:
                from models import Doctor
                doctor = Doctor.query.get(appointment.doctor_id)
                doctor_name = doctor.name if doctor else "Unknown Doctor"
                
                create_notification(
                    appointment.user_id,
                    "Appointment Reminder",
                    f"You have an appointment with Dr. {doctor_name} tomorrow at {appointment.appointment_time.strftime('%H:%M')}",
                    "appointment_reminder",
                    extra_data={
                        "appointment_id": appointment.id,
                        "doctor_name": doctor_name,
                        "appointment_time": appointment.appointment_time.strftime('%H:%M')
                    }
                )
        
        logger.info("Appointment reminders sent successfully")
        
    except Exception as e:
        logger.error(f"Error sending appointment reminders: {str(e)}")

def send_lab_result_notification(user_id, lab_booking_id, results_available=True):
    """
    Send notification when lab results are available
    """
    try:
        if results_available:
            title = "Lab Results Available"
            message = "Your lab test results are now available. Please check your documents."
        else:
            title = "Lab Tests Scheduled"
            message = "Your lab tests have been scheduled. You will be notified when results are available."
        
        create_notification(
            user_id,
            title,
            message,
            "lab_results",
            extra_data={
                "lab_booking_id": lab_booking_id,
                "results_available": results_available
            }
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending lab result notification: {str(e)}")
        return False

def send_care_package_notification(user_id, package_name, notification_type):
    """
    Send care package related notifications
    """
    try:
        if notification_type == 'enrolled':
            title = "Care Package Enrolled"
            message = f"You have been successfully enrolled in the {package_name} care package."
        elif notification_type == 'reminder':
            title = "Care Package Reminder"
            message = f"Don't forget to follow your {package_name} care plan activities."
        elif notification_type == 'expiring':
            title = "Care Package Expiring"
            message = f"Your {package_name} care package will expire soon. Consider renewing."
        else:
            title = "Care Package Update"
            message = f"Update regarding your {package_name} care package."
        
        create_notification(
            user_id,
            title,
            message,
            "care_package",
            extra_data={
                "package_name": package_name,
                "notification_type": notification_type
            }
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending care package notification: {str(e)}")
        return False

def send_emergency_notification(user_id, emergency_type, location=None):
    """
    Send emergency notifications
    """
    try:
        if emergency_type == 'ambulance_dispatched':
            title = "Ambulance Dispatched"
            message = f"An ambulance has been dispatched to your location{': ' + location if location else ''}."
        elif emergency_type == 'emergency_contact_notified':
            title = "Emergency Contact Notified"
            message = "Your emergency contact has been notified of your situation."
        else:
            title = "Emergency Alert"
            message = "Emergency services have been notified."
        
        create_notification(
            user_id,
            title,
            message,
            "emergency",
            extra_data={
                "emergency_type": emergency_type,
                "location": location
            }
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending emergency notification: {str(e)}")
        return False

def cleanup_old_notifications():
    """
    Clean up notifications older than 30 days
    This function should be called by a scheduled job
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        old_notifications = Notification.query.filter(
            Notification.created_at < cutoff_date
        ).all()
        
        for notification in old_notifications:
            db.session.delete(notification)
        
        db.session.commit()
        
        logger.info(f"Cleaned up {len(old_notifications)} old notifications")
        
    except Exception as e:
        logger.error(f"Error cleaning up old notifications: {str(e)}")
        db.session.rollback()
