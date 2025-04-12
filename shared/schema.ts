import { pgTable, text, serial, timestamp, varchar } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const events = pgTable("events", {
  id: serial("id").primaryKey(),
  type: varchar("type", { length: 50 }).notNull(),
  description: text("description").notNull(),
  timestamp: timestamp("timestamp").defaultNow().notNull(),
  objects: text("objects").array()
});

export const alerts = pgTable("alerts", {
  id: serial("id").primaryKey(),
  level: varchar("level", { length: 20 }).notNull(),
  message: text("message").notNull(),
  timestamp: timestamp("timestamp").defaultNow().notNull(),
  acknowledged: boolean("acknowledged").default(false)
});

export const insertEventSchema = createInsertSchema(events).omit({ 
  id: true, 
  timestamp: true 
});

export const insertAlertSchema = createInsertSchema(alerts).omit({ 
  id: true, 
  timestamp: true,
  acknowledged: true 
});

export type InsertEvent = z.infer<typeof insertEventSchema>;
export type Event = typeof events.$inferSelect;
export type Alert = typeof alerts.$inferSelect;
export type InsertAlert = z.infer<typeof insertAlertSchema>;
