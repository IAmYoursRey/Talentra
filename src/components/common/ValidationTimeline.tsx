import React from 'react';
import { ValidationTimelineEvent } from '../../types/portfolio.types';
import { StatusBadge } from './StatusBadge';
import { cn } from '../../lib/utils';
import { User, ShieldCheck, Clock } from 'lucide-react';

interface ValidationTimelineProps {
  events: ValidationTimelineEvent[];
  className?: string;
}

export const ValidationTimeline: React.FC<ValidationTimelineProps> = ({ events, className }) => {
  if (!events || events.length === 0) {
    return <p className="text-xs text-slate-500 italic">Belum ada riwayat aktivitas.</p>;
  }

  return (
    <div className={cn('flow-root', className)}>
      <ul className="-mb-8">
        {events.map((event, idx) => {
          const isLast = idx === events.length - 1;
          const RoleIcon = event.actorRole === 'teacher' ? ShieldCheck : event.actorRole === 'student' ? User : Clock;

          return (
            <li key={event.id || idx}>
              <div className="relative pb-8">
                {!isLast && (
                  <span
                    className="absolute left-4 top-4 -ml-px h-full w-0.5 bg-slate-200"
                    aria-hidden="true"
                  />
                )}
                <div className="relative flex items-start space-x-3">
                  <div className="relative">
                    <div className="h-8 w-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600">
                      <RoleIcon className="w-4 h-4" />
                    </div>
                  </div>
                  <div className="min-w-0 flex-1 pt-0.5">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-slate-900">{event.actorName}</span>
                        <span className="text-[11px] text-slate-500 capitalize bg-slate-100 px-1.5 py-0.5 rounded">
                          {event.actorRole === 'teacher' ? 'Guru Validator' : 'Siswa'}
                        </span>
                      </div>
                      <time className="text-[11px] text-slate-400">{event.timestamp}</time>
                    </div>
                    <div className="mt-1 flex items-center gap-2">
                      <StatusBadge status={event.status} size="sm" />
                    </div>
                    {event.note && (
                      <p className="mt-1.5 text-xs text-slate-600 bg-slate-50 border border-slate-100 rounded-lg p-2.5 leading-relaxed">
                        {event.note}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
};
