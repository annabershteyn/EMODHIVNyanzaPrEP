clear;
filename = 'Nyanza_30_40_50_iter174';
%filename = 'Nyanza_Decl_Inc_iter64';
%filename = 'Nyanza_Decl_Inc_NonResident_Clients_iter59';

load([filename,'.mat'])

% jp is a 250x1 cell array of 1x64 cell arrays. It shows the parameter path
% associated with every value of the table. But, I'm pretty sure each
% column of the table is associated with a specific parameter path. Let's
% check that this is true. If not true, print a warning.

varnames = cell(size(jp{1}));

for param_iter = 1:length(jp{1})
    for row_iter = 1:length(jp)
        
        first_param_name = jp{1}{param_iter};
        curr_param_name  = jp{row_iter}{param_iter};
        
        if not(strcmp(first_param_name,curr_param_name))
            warning([first_param_name, ' does not match ', curr_param_name])
        end
        
    end
    
    
    % now extract just the last field for a quasi-friendly name.
    % this is because table variable names cannot have '.' and must be less
    % than 64 characters long.
    
    param_name_parts = strsplit(curr_param_name,{'.','__KP_','_KP_'});
    
    if strcmpi(param_name_parts{end},'Min') || strcmpi(param_name_parts{end},'Max')|| strcmpi(param_name_parts{end},'Mid')|| strcmpi(param_name_parts{end},'Rate')
        varnames{param_iter}  = [param_name_parts{end-4},'_',param_name_parts{end-3},'_',param_name_parts{end-1},'_',param_name_parts{end}];
        %    elseif strcmpi(param_name_parts{end-1},'LOW') || strcmpi(param_name_parts{end-1},'MEDIUM')|| strcmpi(param_name_parts{end-1},'HIGH');
        %         varnames{param_iter}  = [param_name_parts{end-3},'_',param_name_parts{end},'_',param_name_parts{end-1}];
    elseif (length(param_name_parts)>4) &&  (strcmpi(param_name_parts{end-3},'TRANSITORY') || strcmpi(param_name_parts{end-3},'INFORMAL')|| strcmpi(param_name_parts{end-3},'MARITAL')|| strcmpi(param_name_parts{end-3},'COMMERCIAL'));
        varnames{param_iter}  = [param_name_parts{end-3},'_',param_name_parts{end-1},'_',param_name_parts{end}];
        
    elseif (length(param_name_parts)>3)  && (strcmpi(param_name_parts{end-2},'TRANSITORY') || strcmpi(param_name_parts{end-2},'INFORMAL')|| strcmpi(param_name_parts{end-2},'MARITAL')|| strcmpi(param_name_parts{end-2},'COMMERCIAL'));
        varnames{param_iter}  = [param_name_parts{end-2},'_',param_name_parts{end}];
        
    elseif strcmpi(param_name_parts{end-1},'CONFIG') || strcmpi(param_name_parts{end-1},'CAMPAIGN')|| strcmpi(param_name_parts{end-1},'DEMOGRAPHICS')
        varnames{param_iter}  = param_name_parts{end};
    else
        varnames{param_iter}  = [param_name_parts{end-1},'_',param_name_parts{end}];
    end
    
    
end


% 'vals' is a 250x1 cell array of 1x64 cell arrays of values.
% Let's turn it into a 250x64 table.
% First convert it to a 250x64 cell array, then convert to a table using
% array2table(vals_array,'VariableNames',jp{1})

vals_array = cell(length(vals{1}), length(vals));
for row_iter = 1:length(vals)
    
    curr_row  = vals{row_iter};
    vals_array(:, row_iter) = curr_row;
end

vals_mat = nan(length(vals{1}), length(vals)); % condense risk distributions (LOW/MED/HI) assortativity matrixes (3x3 LOW/MED/HI) into just 1 value

for param_iter = 1:length(jp{1})
    
    curr_col = vals_array(param_iter,:);
    
    
    if length(curr_col{1}) == 3 && iscell(curr_col{1}) && length(curr_col{1}{1}) == 3 % risk assort 3x3 (LOW/MED/HI)  -- use LOW-MEDIUM mixing. Model assumes no LOW-HIGH mixing.
        vals_mat(param_iter,:) = cellfun(@(x) x{1}{2}, curr_col);%risk assort 3x3 (LOW/MED/HI)  -- use LOW-MEDIUM mixing. Model assumes no LOW-HIGH mixing.
    elseif length(curr_col{1}) == 3 % risk distributions (LOW/MED/HI)  -- use proportion MEDIUM -- or male to female rel infectivity multiplier -- use youngest value
         vals_mat(param_iter,:) = cellfun(@(x) x(2), curr_col);
    else
        vals_mat(param_iter,:) = cell2mat(curr_col);
    end
end



vals_array = vals_array';
vals_mat = vals_mat';
%varnames = cellfun(@(x) strrep(x,'.','_'), jp{1}, 'UniformOutput', false);

% create the final table of params and write it to .csv format.

T = array2table(vals_mat,'VariableNames',varnames);
writetable(T,[filename,'.csv'])


fig_h_all_histograms = figure;
set(fig_h_all_histograms, 'color','white')

   
interesting_params = ...
 {  'Defaults_TRANSITORY_Condom_Usage_Probability_Mid',...
    'Defaults_TRANSITORY_Condom_Usage_Probability_Rate',...
    'Defaults_TRANSITORY_Condom_Usage_Probability_Max',...
    'Defaults_INFORMAL_Condom_Usage_Probability_Mid',...
    'Defaults_INFORMAL_Condom_Usage_Probability_Rate',...
    'Defaults_INFORMAL_Condom_Usage_Probability_Max',...
    'Defaults_MARITAL_Condom_Usage_Probability_Mid',...
    'Defaults_MARITAL_Condom_Usage_Probability_Rate',...
    'Defaults_MARITAL_Condom_Usage_Probability_Max'...
};

T_interesting = T(:,interesting_params);


for param_iter = 1:length(interesting_params)
    
    curr_column = table2array(T_interesting(:,param_iter));
    
    subplot(3,3,param_iter)
    histogram(curr_column,15)
    %plot_title = strrep(T_interesting.Properties.VariableNames{param_iter},'_',' ');
    %title(plot_title)
    set(gca,'box','off','ycolor','w') 
end


% it is tempting to make a giant plot of correlations, but 64x64 is a lot!
%plotmatrix(vals_mat) % 

risk_related_params = ...
    { 'Initial_Distribution_Risk_Homa_Bay',...
        'Initial_Distribution_Risk_Siaya',...
        'Initial_Distribution_Risk_Kisumu',...
        'Initial_Distribution_Risk_Migori',...
        'Initial_Distribution_Risk_Nyamira',...
        'Initial_Distribution_Risk_Kisii'};
   


interesting_params = ...
    { 'Base_Infectivity',...
    'Male_To_Female_Relative_Infectivity_Multipliers',...
    'TRANSITORY_Formation_Rate_Constant',...
    'INFORMAL_Formation_Rate_Constant',...
    'MARITAL_Formation_Rate_Constant'};
 

   
interesting_params = ...
 {'Sexual_Debut_Age_Female_Weibull_Scale',...
    'Sexual_Debut_Age_Female_Weibull_Heterogeneity',...
    'Sexual_Debut_Age_Male_Weibull_Scale',...
    'Sexual_Debut_Age_Male_Weibull_Heterogeneity'};

T_risk = T(:,risk_related_params);
if(false)
fig_h_risk_matrix = figure;
plotmatrix(table2array(T_risk));
end

% ah = get(gcf,'children') ;
% xlim = get(ah,'xlim') ;
% xlim = cat(1,xlim{:}) ;
% set(ah,'xlim',[min(xlim(:,1)) max(xlim(:,2))]) ;
% 
% ah = get(gcf,'children') ;
% xlim = get(ah,'xlim') ;
% xlim = cat(1,xlim{:}) ;
% set(ah,'xlim',[min(xlim(:,1)) max(xlim(:,2))]) ;
% set(gcf,'color','white')
varnames';



%% additional figures for model assumption slides


% female age when eligible for first sexual relationship

fig_h_sexual_debut_age_distributions = figure; hold on; set(gcf,'color','w')

T_debut = T(:,{'Sexual_Debut_Age_Female_Weibull_Scale',...
    'Sexual_Debut_Age_Female_Weibull_Heterogeneity'});
M_debut = table2array(T_debut);
x_age = 0:.05:25;
for row_iter = 1:length(M_debut)
    
    plot(x_age, wblpdf(x_age,M_debut(row_iter,1), 1/M_debut(row_iter,2)))
    
end

xlim([5 25])
set(gca,'FontSize',20)
set(gca,'box','off','ycolor','w') 

% male age at sexual debut

fig_h_sexual_debut_age_distribution_male = figure; hold on; set(gcf,'color','w')

T_debut = T(:,{'Sexual_Debut_Age_Male_Weibull_Scale',...
    'Sexual_Debut_Age_Male_Weibull_Heterogeneity'});
M_debut = table2array(T_debut);
x_age = 0:.05:25;
for row_iter = 1:length(M_debut)
    
    plot(x_age, wblpdf(x_age,M_debut(row_iter,1), 1/M_debut(row_iter,2)))
    
end

xlim([5 25])
set(gca,'FontSize',20)
set(gca,'box','off','ycolor','w') 


% male histogram of heterogeneity parameter for age at sexual debut

figure;histogram(table2array(T(:,'Sexual_Debut_Age_Male_Weibull_Heterogeneity')),15);
    set(gca,'box','off','ycolor','w') ; set(gcf,'color','white');set(gca,'FontSize',12);
    
    
% female delay until begin FSW: 0 to 5 year uniform distribution    

figure;plot([0,0,5,5,7],[0,1,1,0,0],'linewidth',10);set(gcf,'color','white');
set(gca,'FontSize',20);set(gca,'box','off','ycolor','w');xlim([0,6]); set(gca,'xtick',([0,1,2,3,4,5,6]));
set(gca,'box','off','ycolor','w') 


    
% male delay until begin clients: 0 to 10 year uniform distribution    

figure;plot([0,0,10,10,12],[0,1,1,0,0],'linewidth',10);set(gcf,'color','white');
set(gca,'FontSize',20);set(gca,'box','off','ycolor','w');xlim([0,12]); set(gca,'xtick',([0,2,4,6,8,10,12]));


% female delay until discontinuing sex work: 5.4 years (95%CI 2-9 years)
% Weibull distributed

plot(0:.1:15,wblpdf(0:.1:15,2215/365,3.312),'linewidth',10);set(gcf,'color','white');
set(gca,'FontSize',20);set(gca,'box','off','ycolor','w');set(gca,'xtick',([0,5,10,15]))
wblcdf(9,2215/365,3.312)

    
% male delay until stop being clients: 2 to  year uniform distribution    

figure;plot([0,2,2,30,30,35],[0,0,1,1,0,0],'linewidth',10);set(gcf,'color','white');
set(gca,'FontSize',20);set(gca,'box','off','ycolor','w');xlim([0,35]); set(gca,'xtick',([0,5,10,15,20,25,30,35]));


% general equation for a sigmoid function

x = -10:.1:10;
plot(x,1./(1+exp(-1*x)),'linewidth',10);set(gcf,'color','white');
set(gca,'FontSize',20);set(gca,'box','off');set(gca,'xtick',[],'ytick',[])


% condom param histograms

fig_h_all_histograms = figure;
set(fig_h_all_histograms, 'color','white')

   
interesting_params = ...
 {  'Defaults_TRANSITORY_Condom_Usage_Probability_Mid',...
    'Defaults_TRANSITORY_Condom_Usage_Probability_Rate',...
    'Defaults_TRANSITORY_Condom_Usage_Probability_Max',...
    'Defaults_INFORMAL_Condom_Usage_Probability_Mid',...
    'Defaults_INFORMAL_Condom_Usage_Probability_Rate',...
    'Defaults_INFORMAL_Condom_Usage_Probability_Max',...
    'Defaults_MARITAL_Condom_Usage_Probability_Mid',...
    'Defaults_MARITAL_Condom_Usage_Probability_Rate',...
    'Defaults_MARITAL_Condom_Usage_Probability_Max'...
};

T_interesting = T(:,interesting_params);

for param_iter = 1:length(interesting_params)
    
    curr_column = table2array(T_interesting(:,param_iter));
    
    subplot(3,3,param_iter)
    histogram(curr_column,15)
    %plot_title = strrep(T_interesting.Properties.VariableNames{param_iter},'_',' ');
    %title(plot_title)
    set(gca,'box','off','ycolor','w')
    
end

subplot(3,3,1);xlim([1990,2010])
subplot(3,3,4);xlim([1990,2010])
subplot(3,3,7);xlim([1990,2010])


% marital condom usage ramps

fig_h_condom_ramps = figure;set(gcf,'color','white')
interesting_params = ...
 { 
    'Defaults_MARITAL_Condom_Usage_Probability_Mid',...
    'Defaults_MARITAL_Condom_Usage_Probability_Rate',...
    'Defaults_MARITAL_Condom_Usage_Probability_Max'...
};

M_marital_condom = table2array(T(:,interesting_params));
x_condom = 1990:.1:2010;
 for row_iter = 1:length(M_marital_condom)
    year = M_marital_condom(row_iter,1);
    rate = M_marital_condom(row_iter,2);
    max = M_marital_condom(row_iter,3);
    plot(x_condom, max./(1+exp(-1*(x_condom-year)/rate))); hold on;
    
 end

set(gca,'FontSize',20);
set(gca,'box','off'); 



% Distribution of transitory and informal “max” by county



fig_h_all_histograms = figure;
set(fig_h_all_histograms, 'color','white')

   
interesting_params = ...
 {  'Homa_Bay_TRANSITORY_Condom_Usage_Probability_Max',...
    'Siaya_TRANSITORY_Condom_Usage_Probability_Max',...
    'Kisumu_TRANSITORY_Condom_Usage_Probability_Max',...
    'Migori_TRANSITORY_Condom_Usage_Probability_Max',...
    'Nyamira_TRANSITORY_Condom_Usage_Probability_Max',...
    'Kisii_TRANSITORY_Condom_Usage_Probability_Max',...
    'Homa_Bay_INFORMAL_Condom_Usage_Probability_Max',...
    'Siaya_INFORMAL_Condom_Usage_Probability_Max',...
    'Kisumu_INFORMAL_Condom_Usage_Probability_Max',...
    'Migori_INFORMAL_Condom_Usage_Probability_Max',...
    'Nyamira_INFORMAL_Condom_Usage_Probability_Max',...
    'Kisii_INFORMAL_Condom_Usage_Probability_Max'...
};

T_interesting = T(:,interesting_params);

for param_iter = 1:length(interesting_params)
    
    curr_column = table2array(T_interesting(:,param_iter));
    
    subplot(2,6,param_iter)
    histogram(curr_column,15)
    %plot_title = strrep(T_interesting.Properties.VariableNames{param_iter},'_',' ');
    %title(plot_title)
    set(gca,'box','off','ycolor','w','xtick',[0,.25,.5],'xticklabel',{'0%','25%','50%'}) 
set(gca,'FontSize',12);
        xlim([0,.5])
 
end





% proportion medium risk histograms

fig_h_all_histograms = figure;
set(fig_h_all_histograms, 'color','white')

   
interesting_params = ...
    { 'Initial_Distribution_Risk_Homa_Bay',...
        'Initial_Distribution_Risk_Siaya',...
        'Initial_Distribution_Risk_Kisumu',...
        'Initial_Distribution_Risk_Migori',...
        'Initial_Distribution_Risk_Nyamira',...
        'Initial_Distribution_Risk_Kisii'};

T_interesting = T(:,interesting_params);

for param_iter = 1:length(interesting_params)
    
    curr_column = table2array(T_interesting(:,param_iter));
    
    subplot(1, 6, param_iter)
    histogram(curr_column,15)
    %plot_title = strrep(T_interesting.Properties.VariableNames{param_iter},'_',' ');
    %title(plot_title)
    set(gca,'box','off','ycolor','w')
    xlim([0,0.6])
    set(gca,'xtick',[0,.2,.4,.6])
   set(gca,'xticklabel',{'0%','20%','40%','60%'})
    set(gca,'FontSize',16);
end





% base and female-to-male infectivity histograms

fig_h_all_histograms = figure;
set(fig_h_all_histograms, 'color','white')

   
interesting_params = ...
    { 'Base_Infectivity',...
        'Male_To_Female_Relative_Infectivity_Multipliers'};

T_interesting = T(:,interesting_params);

for param_iter = 1:length(interesting_params)
    
    curr_column = table2array(T_interesting(:,param_iter));
    
    subplot(1, 2, param_iter)
    histogram(curr_column,15)
    %plot_title = strrep(T_interesting.Properties.VariableNames{param_iter},'_',' ');
    %title(plot_title)
    set(gca,'box','off','ycolor','w')
  %  xlim([0,0.6])
 %   set(gca,'xtick',[0,.2,.4,.6])
%   set(gca,'xticklabel',{'0%','20%','40%','60%'})
    set(gca,'FontSize',16);
end



% male to female risk multiplier


figure;plot([0,15,25,45],[2.0,2.0,1.2,1.2],'linewidth',10);set(gcf,'color','white');
set(gca,'FontSize',20);set(gca,'box','off');xlim([0,45]);ylim([0,2]); set(gca,'xtick',([0,5,10,15,20,25,30,35,40,45]));set(gca,'ytick',([0,1.2]));

