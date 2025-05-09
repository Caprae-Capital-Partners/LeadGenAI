"use client"

import React, { useState } from 'react';
import axios from 'axios';
import { useQuery } from 'react-query';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface Lead {
    name: string;
    website: string;
    industry: string;
    location: string;
    employee_count?: number;
}

interface LeadGenerationProps {
    maxLeads?: number;
    sources?: string[];
}

export function LeadGenerationComponent({
    maxLeads = 20,
    sources = ['apollo', 'growjo', 'linkedin']
}: LeadGenerationProps): React.ReactElement {
    const [industry, setIndustry] = useState<string>('');
    const [location, setLocation] = useState<string>('');
    const [leadCount, setLeadCount] = useState<number>(maxLeads);

    const { 
        data: leads = [], 
        isLoading, 
        error, 
        refetch 
    } = useQuery<Lead[]>(
        ['generateLeads', { industry, location, leadCount, sources }],
        async () => {
            const response = await axios.get('/api/generate/leads', {
                params: { 
                    industry, 
                    location, 
                    max_leads: leadCount,
                    sources: sources.join(',')
                }
            });
            return response.data || [];
        },
        {
            enabled: false,
            refetchOnWindowFocus: false,
            retry: 2,
            placeholderData: []
        }
    );

    const generateLeads = (): void => {
        if (industry && location) {
            refetch();
        }
    };

    const industryOptions: string[] = [
        'Technology', 'Finance', 'Healthcare', 
        'Retail', 'Education', 'Manufacturing'
    ];

    return (
        <div className="container mx-auto p-4">
            <Card>
                <CardHeader>
                    <CardTitle>Lead Generation</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-3 gap-4 mb-4">
                        <Select 
                            value={industry}
                            onValueChange={(value: string) => setIndustry(value)}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="Select Industry" />
                            </SelectTrigger>
                            <SelectContent>
                                {industryOptions.map((ind: string) => (
                                    <SelectItem key={ind} value={ind}>
                                        {ind}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>

                        <Input 
                            placeholder="Location (e.g., San Francisco)" 
                            value={location}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setLocation(e.target.value)}
                        />

                        <Select 
                            value={leadCount.toString()} 
                            onValueChange={(value: string) => setLeadCount(parseInt(value))}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="Max Leads" />
                            </SelectTrigger>
                            <SelectContent>
                                {[5, 10, 15, 20, 30, 50].map((num: number) => (
                                    <SelectItem key={num} value={num.toString()}>
                                        {num} Leads
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                    
                    <Button 
                        onClick={generateLeads} 
                        disabled={isLoading || !industry || !location}
                        className="w-full"
                    >
                        {isLoading ? 'Generating Leads...' : 'Generate Leads'}
                    </Button>

                    {error !== null && error !== undefined && (
                        <div className="text-red-500 mt-4">
                            {typeof error === 'string' 
                                ? error 
                                : 'Error generating leads. Please try again.'}
                        </div>
                    )}

                    {leads.length > 0 && (
                        <div className="mt-4">
                            <h3 className="text-lg font-semibold mb-2">Generated Leads</h3>
                            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {leads.map((lead: Lead, index: number): React.ReactElement => (
                                    <Card key={`lead-${index}`}>
                                        <CardContent className="pt-4">
                                            <h4 className="font-bold">{String(lead.name || 'Unnamed Lead')}</h4>
                                            <p>Website: {String(lead.website || 'N/A')}</p>
                                            <p>Industry: {String(lead.industry || 'Unspecified')}</p>
                                            <p>Location: {String(lead.location || 'Unknown')}</p>
                                            {lead.employee_count !== undefined && (
                                                <p>Employees: {String(lead.employee_count)}</p>
                                            )}
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
