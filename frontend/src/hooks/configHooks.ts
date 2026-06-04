import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { configService, SystemConfig } from '../services/configService';
import toast from 'react-hot-toast';

export const useConfig = () => {
  return useQuery({
    queryKey: ['config'],
    queryFn: configService.getConfig,
    refetchOnWindowFocus: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useUpdateConfig = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: Partial<SystemConfig>) => configService.updateConfig(payload),
    onSuccess: () => {
      toast.success("Configuration updated and saved to PostgreSQL successfully!");
      queryClient.invalidateQueries({ queryKey: ['config'] });
      queryClient.invalidateQueries({ queryKey: ['audit-logs'] });
    },
    onError: (error: any) => {
      toast.error(`Error saving: ${error.message || 'Unknown error occurred'}`);
    }
  });
};

export const useInstagramTest = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: configService.testInstagram,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audit-logs'] });
    },
    onError: (error: any) => {
      toast.error(`Connection test failed: ${error.message || 'Unknown error'}`);
    }
  });
};

export const useAuditLogs = () => {
  return useQuery({
    queryKey: ['audit-logs'],
    queryFn: configService.getAuditLogs,
    staleTime: 60 * 1000,
  });
};

export const useHealthStatus = () => {
  return useQuery({
    queryKey: ['health-status'],
    queryFn: configService.getHealthStatus,
    refetchInterval: 30000, // Auto-refresh every 30s
    staleTime: 15 * 1000,
  });
};
