import { Event, Alert, InsertEvent, InsertAlert } from "@shared/schema";

export interface IStorage {
  createEvent(event: InsertEvent): Promise<Event>;
  getEvents(limit?: number): Promise<Event[]>;
  createAlert(alert: InsertAlert): Promise<Alert>;
  getAlerts(limit?: number): Promise<Alert[]>;
  acknowledgeAlert(id: number): Promise<Alert | undefined>;
}

export class MemStorage implements IStorage {
  private events: Map<number, Event>;
  private alerts: Map<number, Alert>;
  private eventId: number;
  private alertId: number;

  constructor() {
    this.events = new Map();
    this.alerts = new Map();
    this.eventId = 1;
    this.alertId = 1;
  }

  async createEvent(insertEvent: InsertEvent): Promise<Event> {
    const id = this.eventId++;
    const event: Event = {
      ...insertEvent,
      id,
      timestamp: new Date(),
    };
    this.events.set(id, event);
    return event;
  }

  async getEvents(limit = 100): Promise<Event[]> {
    return Array.from(this.events.values())
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      .slice(0, limit);
  }

  async createAlert(insertAlert: InsertAlert): Promise<Alert> {
    const id = this.alertId++;
    const alert: Alert = {
      ...insertAlert,
      id,
      timestamp: new Date(),
      acknowledged: false
    };
    this.alerts.set(id, alert);
    return alert;
  }

  async getAlerts(limit = 100): Promise<Alert[]> {
    return Array.from(this.alerts.values())
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      .slice(0, limit);
  }

  async acknowledgeAlert(id: number): Promise<Alert | undefined> {
    const alert = this.alerts.get(id);
    if (alert) {
      const updated = { ...alert, acknowledged: true };
      this.alerts.set(id, updated);
      return updated;
    }
    return undefined;
  }
}

export const storage = new MemStorage();
