import React, { useEffect, useState } from 'react';
import {
    Drawer, Box, Typography, Divider, FormControl,
    InputLabel, Select, MenuItem, TextField, Button, CircularProgress, Alert
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { api } from '@services/api';

interface FormData {
    model_provider: string;
    model_name: string;
    api_key: string;
    provider_endpoint: string;
    model_params?: Record<string, unknown>
}

interface ConfigDrawerProps {
    open: boolean;
    onClose: () => void;
    checkModel: () => void;
    providerModels: Record<string, Record<string, string>>;
}

export const ConfigDrawer: React.FC<ConfigDrawerProps> = ({
    open, onClose, checkModel, providerModels
}) => {
    const { control, handleSubmit, watch, setValue } = useForm<FormData>({
        defaultValues: {
            model_provider: '',
            model_name: '',
            api_key: '',
            provider_endpoint: '',
            model_params: {
                project_id: ''
            }
        }
    });

    const selectedProvider = watch('model_provider');

    useEffect(() => {
        if (selectedProvider === 'IBM') {
            setValue('provider_endpoint', 'https://us-south.ml.cloud.ibm.com', {
                shouldValidate: true,
                shouldDirty: true,
            });
        } else {
            setValue('provider_endpoint', '', { shouldValidate: true, shouldDirty: true });
        }
    }, [selectedProvider, setValue]);

    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const onSubmit = async (data: FormData) => {
        setLoading(true);
        setMessage(null);
        try {
            const res = await api.post('/config', data);
            setMessage({ type: 'success', text: 'Configuration saved successfully!' });

            setTimeout(() => {
                setMessage(null);
                checkModel();
                onClose();
            }, 2000);

        } catch (error: any) {
            console.error(error);

            let errorText = 'Failed to save configuration.';
            if (error?.response?.data?.details) {
                errorText = error.response.data.details;
            } else if (error?.message) {
                errorText = error.message;
            }

            setMessage({ type: 'error', text: errorText });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Drawer anchor="left" open={open} onClose={onClose}>
            <Box sx={{ width: 300, p: 2 }}>
                <Typography variant="h6">Configuration</Typography>
                <Divider sx={{ my: 2 }} />

                <form onSubmit={handleSubmit(onSubmit)}>
                    <FormControl fullWidth sx={{ mb: 2 }}>
                        <InputLabel>Provider</InputLabel>
                        <Controller
                            name="model_provider"
                            control={control}
                            render={({ field }) => (
                                <Select {...field} label="Provider">
                                    {Object.keys(providerModels).map((prov) => (
                                        <MenuItem key={prov} value={prov}>{prov}</MenuItem>
                                    ))}
                                </Select>
                            )}
                        />
                    </FormControl>

                    {selectedProvider && (
                        <FormControl fullWidth sx={{ mb: 2 }}>
                            <InputLabel>Model</InputLabel>
                            <Controller
                                name="model_name"
                                control={control}
                                render={({ field }) => (
                                    <Select {...field} label="Model">
                                        {Object.entries(providerModels[selectedProvider]).map((m) => (
                                            <MenuItem key={m[0]} value={m[1]}>{m[0]}</MenuItem>
                                        ))}
                                    </Select>
                                )}
                            />
                        </FormControl>
                    )}

                    {selectedProvider === 'IBM' && (
                        <Controller
                            name="model_params.project_id"
                            control={control}
                            rules={{ required: 'Project ID is required' }}
                            render={({ field, fieldState }) => (
                                <TextField
                                    {...field}
                                    type="password"
                                    label="Project ID"
                                    fullWidth
                                    sx={{ mb: 2 }}
                                    error={!!fieldState.error}
                                    helperText={fieldState.error?.message}
                                />
                            )}
                        />
                    )}

                    <Controller
                        name="api_key"
                        control={control}
                        rules={{ required: 'API Key is required' }}
                        render={({ field, fieldState }) => (
                            <TextField
                                {...field}
                                label="API Key"
                                type="password"
                                fullWidth
                                sx={{ mb: 2 }}
                                error={!!fieldState.error}
                                helperText={fieldState.error?.message}
                            />
                        )}
                    />
                    <Controller
                        name="provider_endpoint"
                        control={control}
                        rules={{ required: 'Endpoint is required' }}
                        render={({ field, fieldState }) => (
                            <TextField
                                {...field}
                                label="Provider endpoint"
                                fullWidth
                                sx={{ mb: 2 }}
                                error={!!fieldState.error}
                                helperText={fieldState.error?.message}
                            />
                        )}
                    />

                    {message && (
                        <Alert severity={message.type} sx={{ mb: 2 }}>
                            {message.text}
                        </Alert>
                    )}

                    <Button type="submit" variant="contained" color="primary" fullWidth disabled={loading}>
                        {loading ? <CircularProgress size={24} /> : 'Save'}
                    </Button>
                </form>
            </Box>
        </Drawer>
    );
};
