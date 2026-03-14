'use client';

import {
  AreaSeries,
  type AreaSeriesOptions,
  ColorType,
  createChart,
  HistogramSeries,
  type IChartApi,
  type ISeriesApi,
} from 'lightweight-charts';
import { useLayoutEffect, useRef } from 'react';

interface EquityCurvePoint {
  time: string;
  value: number;
}

interface RegimePeriodProp {
  start: string;
  end: string;
  regime: string;
}

interface EquityCurveProps {
  data: EquityCurvePoint[];
  regimePeriods: RegimePeriodProp[];
}

const REGIME_COLORS: Record<string, string> = {
  Bull: 'rgba(0,200,83,0.08)',
  Bear: 'rgba(255,82,82,0.08)',
  Accumulation: 'rgba(79,195,247,0.08)',
  Distribution: 'rgba(255,183,77,0.08)',
  Unknown: 'rgba(128,128,128,0.05)',
};

function getRegimeColor(regime: string): string {
  return REGIME_COLORS[regime] ?? REGIME_COLORS.Unknown;
}

export function EquityCurve({ data, regimePeriods }: EquityCurveProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    const chart: IChartApi = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#9ca3af',
        fontFamily: 'JetBrains Mono, monospace',
      },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.04)' },
        horzLines: { color: 'rgba(255,255,255,0.04)' },
      },
      height: 300,
      handleScroll: false,
      handleScale: false,
    });

    let isRemoved = false;

    const areaSer: ISeriesApi<'Area'> = chart.addSeries(AreaSeries, {
      lineColor: '#4fc3f7',
      topColor: 'rgba(79,195,247,0.25)',
      bottomColor: 'rgba(79,195,247,0.0)',
      lineWidth: 2,
    } as Partial<AreaSeriesOptions>);

    areaSer.setData(data);

    if (regimePeriods.length > 0) {
      const histSer = chart.addSeries(HistogramSeries, {
        priceScaleId: '',
        color: 'rgba(128,128,128,0.05)',
      });

      histSer.priceScale().applyOptions({
        scaleMargins: { top: 0, bottom: 0 },
      });

      const regimeData = data.map((point) => {
        const date = point.time;
        let color = REGIME_COLORS.Unknown;
        for (const period of regimePeriods) {
          if (date >= period.start && date <= period.end) {
            color = getRegimeColor(period.regime);
            break;
          }
        }
        return { time: point.time, value: 1, color };
      });

      histSer.setData(regimeData);
    }

    chart.timeScale().fitContent();

    const ro = new ResizeObserver((entries) => {
      if (isRemoved) return;
      for (const entry of entries) {
        chart.applyOptions({ width: entry.contentRect.width });
      }
    });

    ro.observe(containerRef.current);

    return () => {
      isRemoved = true;
      ro.disconnect();
      chart.remove();
    };
  }, [data, regimePeriods]);

  if (data.length === 0) {
    return <p className="py-8 text-center text-muted-foreground">No equity data</p>;
  }

  return <div ref={containerRef} className="w-full" />;
}
