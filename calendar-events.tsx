import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const CalendarEventGenerator = () => {
  const events = [
    {
      summary: "GS Setup",
      start: { dateTime: "2025-02-17T07:00:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-17T22:00:00", timeZone: "America/New_York" }
    },
    {
      summary: "Get bottled water and snacks to AV Team",
      start: { dateTime: "2025-02-17T08:00:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-17T09:00:00", timeZone: "America/New_York" }
    },
    {
      summary: "Setup power strips and extension cords in Conference Services Desk and Staff Office",
      start: { dateTime: "2025-02-17T08:00:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-17T12:00:00", timeZone: "America/New_York" }
    },
    {
      summary: "Envirographics Install",
      start: { dateTime: "2025-02-17T08:00:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-17T17:00:00", timeZone: "America/New_York" }
    },
    {
      summary: "KA Connect Setup (hanging sign, carpet, floor signs)",
      start: { dateTime: "2025-02-17T09:30:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-17T10:30:00", timeZone: "America/New_York" }
    },
    {
      summary: "Staff Dinner for 36 (Please let me know if you can't attend)",
      start: { dateTime: "2025-02-17T18:00:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-17T20:00:00", timeZone: "America/New_York" }
    },
    // February 18
    {
      summary: "Setup power strips and extension cords in Exec Office",
      start: { dateTime: "2025-02-18T08:00:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-18T12:00:00", timeZone: "America/New_York" }
    },
    {
      summary: "Staff Lunch and Staff Meeting",
      start: { dateTime: "2025-02-18T12:00:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-18T13:00:00", timeZone: "America/New_York" }
    },
    {
      summary: "Staff Picture, Tour of Space, and Conference Check-In",
      start: { dateTime: "2025-02-18T13:00:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-18T13:30:00", timeZone: "America/New_York" }
    },
    {
      summary: "Confirm that speaker tables (from Orchestrate) are in Cypress 3 and Royal",
      start: { dateTime: "2025-02-18T15:00:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-18T15:30:00", timeZone: "America/New_York" }
    },
    {
      summary: "Prayer Walk",
      start: { dateTime: "2025-02-18T15:30:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-18T16:00:00", timeZone: "America/New_York" }
    },
    {
      summary: "Staff Dinner",
      start: { dateTime: "2025-02-18T17:00:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-18T17:45:00", timeZone: "America/New_York" }
    },
    {
      summary: "First-Time Attendee Team Meeting",
      start: { dateTime: "2025-02-18T17:45:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-18T18:30:00", timeZone: "America/New_York" }
    },
    {
      summary: "App Support",
      description: "Please be proactive in going through the line to make sure that everyone has the app open before checking in and to see if anyone has any issues",
      start: { dateTime: "2025-02-18T18:30:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-18T20:00:00", timeZone: "America/New_York" }
    },
    // February 19
    {
      summary: "KA Staff Meeting and Prayer",
      start: { dateTime: "2025-02-19T06:45:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-19T07:00:00", timeZone: "America/New_York" }
    },
    {
      summary: "Provide Audio for Exhibitor Meeting",
      start: { dateTime: "2025-02-19T09:30:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-19T10:30:00", timeZone: "America/New_York" }
    },
    {
      summary: "Run AV (sound and mics only) for Women's CG meeting",
      start: { dateTime: "2025-02-19T14:45:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-19T15:30:00", timeZone: "America/New_York" }
    },
    {
      summary: "Provide Audio for Women's Meetup",
      start: { dateTime: "2025-02-19T15:00:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-19T15:30:00", timeZone: "America/New_York" }
    },
    {
      summary: "Walk Yellow Couch Participants to Taping",
      start: { dateTime: "2025-02-19T16:30:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-19T17:00:00", timeZone: "America/New_York" }
    },
    {
      summary: "GS2: Make sure doors are locked",
      start: { dateTime: "2025-02-19T17:00:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-19T17:45:00", timeZone: "America/New_York" }
    },
    {
      summary: "Production Crew Dinner (GS Crew)",
      start: { dateTime: "2025-02-19T17:45:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-19T18:45:00", timeZone: "America/New_York" }
    },
    // February 20
    {
      summary: "Staff Meeting and Prayer",
      start: { dateTime: "2025-02-20T06:30:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-20T06:40:00", timeZone: "America/New_York" }
    },
    {
      summary: "Collect Wow! Packages leftover",
      start: { dateTime: "2025-02-20T10:00:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-20T10:30:00", timeZone: "America/New_York" }
    },
    {
      summary: "Escort Kitces to Super Breakout (Royal)",
      start: { dateTime: "2025-02-20T10:00:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-20T10:05:00", timeZone: "America/New_York" }
    },
    {
      summary: "Provide audio for Emerging Advisors Meetup",
      start: { dateTime: "2025-02-20T16:15:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-20T16:45:00", timeZone: "America/New_York" }
    },
    {
      summary: "GS2: Make sure doors are locked",
      start: { dateTime: "2025-02-20T17:00:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-20T17:45:00", timeZone: "America/New_York" }
    },
    // February 21
    {
      summary: "Line up along Main Hallway between Mag Lawn and Cypress Atrium to wave goodbye",
      description: "We may move this location onsite (Only if you are available)",
      start: { dateTime: "2025-02-21T12:00:00", timeZone: "America/New_York" },
      end: { dateTime: "2025-02-21T12:15:00", timeZone: "America/New_York" }
    }
  ];

  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(events, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className="w-full max-w-4xl">
      <CardContent className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Calendar Events</h2>
          <Button 
            onClick={handleCopy}
            className="bg-blue-500 hover:bg-blue-600 text-white"
          >
            {copied ? 'Copied!' : 'Copy JSON'}
          </Button>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg overflow-auto max-h-96">
          <pre className="text-sm">
            {JSON.stringify(events, null, 2)}
          </pre>
        </div>
      </CardContent>
    </Card>
  );
};

export default CalendarEventGenerator;